import uuid
from datetime import datetime, timedelta, timezone

import jwt
from fastapi.testclient import TestClient

from app import models
from app.database import SessionLocal
from app.main import app
from app.security import ALGORITHM, JWT_SECRET, hash_password

client = TestClient(app)


def _uid(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


def _headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _cleanup(email: str, org_name: str) -> None:
    db = SessionLocal()
    try:
        user = db.query(models.User).filter_by(email=email.lower()).first()
        if user is not None:
            db.query(models.Membership).filter_by(user_id=user.id).delete()
            db.delete(user)
        org = db.query(models.Organization).filter_by(name=org_name).first()
        if org is not None:
            db.delete(org)
        db.commit()
    finally:
        db.close()


def _signup(email: str, password: str, org_name: str, role: str) -> dict:
    resp = client.post(
        "/auth/signup",
        json={
            "email": email,
            "password": password,
            "full_name": "Auth Test",
            "organization_name": org_name,
            "role": role,
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def _login(email: str, password: str) -> dict:
    resp = client.post("/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()


def _make_admin() -> tuple[str, str, str]:
    email = f"{_uid('admin')}@example.com"
    org_name = _uid("org")
    password = "admin-pass-123"
    db = SessionLocal()
    try:
        org = models.Organization(name=org_name)
        db.add(org)
        db.flush()
        db.add(
            models.User(
                email=email, password_hash=hash_password(password), full_name="Admin"
            )
        )
        db.flush()
        user = db.query(models.User).filter_by(email=email).first()
        db.add(
            models.Membership(
                user_id=user.id, organization_id=org.id, role="admin"
            )
        )
        db.commit()
    finally:
        db.close()
    return email, password, org_name


def test_me_returns_user_with_role():
    email = f"{_uid('me')}@example.com"
    org_name = _uid("org")
    _signup(email, "secret123", org_name, "approver")
    try:
        token = _login(email, "secret123")["access_token"]
        resp = client.get("/auth/me", headers=_headers(token))
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["email"] == email
        assert body["role"] == "approver"
        assert "id" in body
    finally:
        _cleanup(email, org_name)


def test_me_missing_token_401():
    resp = client.get("/auth/me")
    assert resp.status_code == 401
    assert "password" not in resp.text


def test_me_invalid_token_401():
    resp = client.get("/auth/me", headers=_headers("not-a-real-token"))
    assert resp.status_code == 401


def test_me_expired_token_401():
    expired = jwt.encode(
        {
            "sub": "1",
            "exp": datetime.now(timezone.utc) - timedelta(minutes=5),
        },
        JWT_SECRET,
        algorithm=ALGORITHM,
    )
    resp = client.get("/auth/me", headers=_headers(expired))
    assert resp.status_code == 401


def test_logout_tells_client_to_discard_token():
    resp = client.post("/auth/logout")
    assert resp.status_code == 200
    assert "discard" in resp.json()["message"].lower()


def test_admin_users_forbidden_for_analyst():
    email = f"{_uid('an')}@example.com"
    org_name = _uid("org")
    _signup(email, "secret123", org_name, "analyst")
    try:
        token = _login(email, "secret123")["access_token"]
        resp = client.get("/admin/users", headers=_headers(token))
        assert resp.status_code == 403
    finally:
        _cleanup(email, org_name)


def test_admin_users_ok_for_admin_and_no_password_hash():
    email, password, org_name = _make_admin()
    try:
        token = _login(email, password)["access_token"]
        resp = client.get("/admin/users", headers=_headers(token))
        assert resp.status_code == 200, resp.text
        users = resp.json()
        assert any(u["email"] == email for u in users)
        for u in users:
            assert "password_hash" not in u
    finally:
        _cleanup(email, org_name)


def test_signup_201_lowercases_email_no_password_hash():
    email = f"MiXeD-{_uid('su')}@Example.COM"
    org_name = _uid("org")
    try:
        body = _signup(email, "secret123", org_name, "analyst")
        assert body["email"] == email.lower()
        assert "password_hash" not in body
        assert "password" not in body
    finally:
        _cleanup(email, org_name)


def test_signup_duplicate_email_409():
    email = f"{_uid('dup')}@example.com"
    org_name = _uid("org")
    try:
        _signup(email, "secret123", org_name, "analyst")
        resp = client.post(
            "/auth/signup",
            json={
                "email": email,
                "password": "secret123",
                "full_name": "Dup",
                "organization_name": org_name,
                "role": "analyst",
            },
        )
        assert resp.status_code == 409
    finally:
        _cleanup(email, org_name)


def test_signup_invalid_role_422():
    email = f"{_uid('role')}@example.com"
    org_name = _uid("org")
    try:
        for bad_role in ("admin", "boss"):
            resp = client.post(
                "/auth/signup",
                json={
                    "email": email,
                    "password": "secret123",
                    "full_name": "R",
                    "organization_name": org_name,
                    "role": bad_role,
                },
            )
            assert resp.status_code == 422, (bad_role, resp.text)
    finally:
        _cleanup(email, org_name)


def test_signup_short_password_422():
    email = f"{_uid('short')}@example.com"
    org_name = _uid("org")
    try:
        resp = client.post(
            "/auth/signup",
            json={
                "email": email,
                "password": "short7",
                "full_name": "S",
                "organization_name": org_name,
                "role": "analyst",
            },
        )
        assert resp.status_code == 422
    finally:
        _cleanup(email, org_name)


def test_login_correct_password_200_with_token():
    email = f"{_uid('ok')}@example.com"
    org_name = _uid("org")
    _signup(email, "secret123", org_name, "analyst")
    try:
        resp = client.post(
            "/auth/login", json={"email": email, "password": "secret123"}
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["access_token"]
        assert body["token_type"] == "bearer"
    finally:
        _cleanup(email, org_name)


def test_login_wrong_password_401():
    email = f"{_uid('wp')}@example.com"
    org_name = _uid("org")
    _signup(email, "secret123", org_name, "analyst")
    try:
        resp = client.post(
            "/auth/login", json={"email": email, "password": "wrong-pass-1"}
        )
        assert resp.status_code == 401
    finally:
        _cleanup(email, org_name)


def test_login_unknown_email_401_same_message_as_wrong_password():
    email = f"{_uid('unk')}@example.com"
    org_name = _uid("org")
    _signup(email, "secret123", org_name, "analyst")
    try:
        wrong_pw = client.post(
            "/auth/login", json={"email": email, "password": "wrong-pass-1"}
        )
        unknown = client.post(
            "/auth/login",
            json={
                "email": f"{_uid('nope')}@example.com",
                "password": "secret123",
            },
        )
        assert wrong_pw.status_code == 401
        assert unknown.status_code == 401
        assert wrong_pw.json() == unknown.json()
    finally:
        _cleanup(email, org_name)
