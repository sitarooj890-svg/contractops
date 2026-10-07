from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .database import SessionLocal
from .models import Membership, Organization, User
from .security import hash_password

router = APIRouter(prefix="/auth", tags=["auth"])


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
