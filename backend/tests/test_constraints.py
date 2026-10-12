import uuid

import pytest
from sqlalchemy.exc import IntegrityError

from app import models
from app.database import SessionLocal


def _uid(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


@pytest.fixture()
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


def _make_user(db, email=None):
    user = models.User(
        email=email or f"{_uid('user')}@example.com",
        password_hash="hash",
        full_name="Test User",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _make_org(db):
    org = models.Organization(name=_uid("org"))
    db.add(org)
    db.commit()
    db.refresh(org)
    return org


def _make_contract(db, org, user):
    contract = models.Contract(
        organization_id=org.id,
        title="Test Contract",
        created_by=user.id,
    )
    db.add(contract)
    db.commit()
    db.refresh(contract)
    return contract


def test_duplicate_user_email_fails(db):
    email = f"{_uid('dup')}@example.com"
    user = _make_user(db, email=email)
    try:
        db.add(
            models.User(
                email=email, password_hash="hash2", full_name="Other"
            )
        )
        with pytest.raises(IntegrityError) as exc_info:
            db.commit()
        assert "uq_users_email" in str(exc_info.value.orig)
    finally:
        db.rollback()
        db.delete(user)
        db.commit()


def test_membership_invalid_role_fails(db):
    user = _make_user(db)
    org = _make_org(db)
    try:
        db.add(
            models.Membership(user_id=user.id, organization_id=org.id, role="boss")
        )
        with pytest.raises(IntegrityError) as exc_info:
            db.commit()
        assert "ck_memberships_role_valid" in str(exc_info.value.orig)
    finally:
        db.rollback()
        db.delete(user)
        db.delete(org)
        db.commit()


def test_contract_bad_organization_fails(db):
    user = _make_user(db)
    try:
        db.add(
            models.Contract(
                organization_id=999999,
                title="Bad Org",
                created_by=user.id,
            )
        )
        with pytest.raises(IntegrityError) as exc_info:
            db.commit()
        assert "fk_contracts_organization_id_organizations" in str(
            exc_info.value.orig
        )
    finally:
        db.rollback()
        db.delete(user)
        db.commit()


def test_obligation_bad_status_fails(db):
    user = _make_user(db)
    org = _make_org(db)
    contract = _make_contract(db, org, user)
    try:
        db.add(
            models.Obligation(
                contract_id=contract.id,
                description="Test",
                status="unknown",
                created_by=user.id,
            )
        )
        with pytest.raises(IntegrityError) as exc_info:
            db.commit()
        assert "ck_obligations_status_valid" in str(exc_info.value.orig)
    finally:
        db.rollback()
        db.delete(contract)
        db.delete(org)
        db.delete(user)
        db.commit()


def test_duplicate_document_version_fails(db):
    user = _make_user(db)
    org = _make_org(db)
    contract = _make_contract(db, org, user)
    v1 = models.DocumentVersion(
        contract_id=contract.id,
        version_number=1,
        file_name="v1.pdf",
        file_path="storage/v1.pdf",
    )
    db.add(v1)
    db.commit()
    try:
        db.add(
            models.DocumentVersion(
                contract_id=contract.id,
                version_number=1,
                file_name="dup.pdf",
                file_path="storage/dup.pdf",
            )
        )
        with pytest.raises(IntegrityError) as exc_info:
            db.commit()
        assert "uq_document_versions_contract_version" in str(
            exc_info.value.orig
        )
    finally:
        db.rollback()
        db.query(models.DocumentVersion).filter_by(contract_id=contract.id).delete()
        db.delete(contract)
        db.delete(org)
        db.delete(user)
        db.commit()


def test_approval_bad_action_fails(db):
    user = _make_user(db)
    org = _make_org(db)
    contract = _make_contract(db, org, user)
    obligation = models.Obligation(
        contract_id=contract.id,
        description="To approve",
        status="draft",
        created_by=user.id,
    )
    db.add(obligation)
    db.commit()
    try:
        db.add(
            models.Approval(
                obligation_id=obligation.id, approver_id=user.id, action="maybe"
            )
        )
        with pytest.raises(IntegrityError) as exc_info:
            db.commit()
        assert "ck_approvals_action_valid" in str(exc_info.value.orig)
    finally:
        db.rollback()
        db.query(models.Approval).filter_by(obligation_id=obligation.id).delete()
        db.delete(obligation)
        db.delete(contract)
        db.delete(org)
        db.delete(user)
        db.commit()
