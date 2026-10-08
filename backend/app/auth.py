from datetime import datetime
from typing import Literal

import jwt
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .database import SessionLocal
from .models import Membership, Organization, User
from .security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])
admin_router = APIRouter(prefix="/admin", tags=["admin"])

bearer_scheme = HTTPBearer(auto_error=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class SignupIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    full_name: str = Field(min_length=1, max_length=255)
    organization_name: str = Field(min_length=1, max_length=255)
    role: Literal["analyst", "approver"]


class SignupOut(BaseModel):
    id: int
    email: str
    full_name: str
    organization_id: int
    organization_name: str
    role: str


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class LoginOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    email: str
    role: str


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    # 401 vs 403: 401 = we do not know who you are (token missing, invalid or
    # expired). 403 = we know who you are, but your role may not do this.
    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        user_id = decode_access_token(credentials.credentials)
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def current_role(db: Session, user: User) -> str:
    membership = (
        db.query(Membership)
        .filter_by(user_id=user.id)
        .order_by(Membership.id)
        .first()
    )
    return membership.role if membership is not None else ""


def require_role(*allowed_roles: str):
    """Dependency factory: 403 when the DB role is not in allowed_roles."""

    def dependency(
        user: User = Depends(get_current_user), db: Session = Depends(get_db)
    ) -> User:
        # Role comes from memberships table, never from the token payload.
        if current_role(db, user) not in allowed_roles:
            raise HTTPException(status_code=403, detail="Forbidden for this role")
        return user

    return dependency


class MeOut(BaseModel):
    id: int
    email: str
    full_name: str
    role: str


class LogoutOut(BaseModel):
    message: str


class AdminUserOut(BaseModel):
    id: int
    email: str
    full_name: str
    created_at: datetime


@router.post("/signup", response_model=SignupOut, status_code=201)
def signup(payload: SignupIn, db: Session = Depends(get_db)):
    email = payload.email.lower().strip()

    existing = db.query(User).filter_by(email=email).first()
    if existing is not None:
        raise HTTPException(status_code=409, detail="Email already exists")

    org_name = payload.organization_name.strip()
    org = db.query(Organization).filter_by(name=org_name).first()
    if org is None:
        org = Organization(name=org_name)
        db.add(org)
        db.flush()

    user = User(
        email=email,
        password_hash=hash_password(payload.password),
        full_name=payload.full_name.strip(),
    )
    db.add(user)
    db.flush()

    db.add(
        Membership(user_id=user.id, organization_id=org.id, role=payload.role)
    )
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Email already exists")

    db.refresh(user)
    db.refresh(org)
    return SignupOut(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        organization_id=org.id,
        organization_name=org.name,
        role=payload.role,
    )


@router.post("/login", response_model=LoginOut)
def login(payload: LoginIn, db: Session = Depends(get_db)):
    email = payload.email.lower().strip()
    user = db.query(User).filter_by(email=email).first()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    membership_role = current_role(db, user)
    return LoginOut(
        access_token=create_access_token(user.id),
        token_type="bearer",
        email=user.email,
        role=membership_role,
    )


@router.get("/me", response_model=MeOut)
def me(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return MeOut(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=current_role(db, user),
    )


@router.post("/logout", response_model=LogoutOut)
def logout():
    # JWT is stateless: the server cannot revoke it. The client must discard it.
    return LogoutOut(
        message="Token received. Discard it on the client and stop sending it."
    )


@admin_router.get("/users", response_model=list[AdminUserOut])
def admin_users(
    _: User = Depends(require_role("admin")), db: Session = Depends(get_db)
):
    users = db.query(User).order_by(User.id).all()
    return [
        AdminUserOut(
            id=u.id,
            email=u.email,
            full_name=u.full_name,
            created_at=u.created_at,
        )
        for u in users
    ]
