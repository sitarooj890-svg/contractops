import uuid
from pathlib import Path

from fastapi.testclient import TestClient

from app import models
from app.database import SessionLocal
from app.main import app
from app.routers.contracts import STORAGE_DIR
from app.security import hash_password

client = TestClient(app)

PASSWORD = "secret123"


def _uid(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


def _headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _signup(email: str, org_name: str, role: str) -> None:
    resp = client.post(
        "/auth/signup",
        json={
            "email": email,
            "password": PASSWORD,
            "full_name": "Contracts Test",
            "organization_name": org_name,
            "role": role,
        },
    )
    assert resp.status_code == 201, resp.text


def _make_admin(email: str, org_name: str) -> None:
    db = SessionLocal()
    try:
        org = db.query(models.Organization).filter_by(name=org_name).first()
        assert org is not None, f"organization {org_name} must exist first"
        db.add(
            models.User(
                email=email, password_hash=hash_password(PASSWORD), full_name="Admin"
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


def _login(email: str) -> str:
    resp = client.post(
        "/auth/login", json={"email": email, "password": PASSWORD}
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def _unlink_version_file(path: str | None) -> None:
    """Remove an uploaded test file, but only inside the storage directory."""
    if not path:
        return
    try:
        target = Path(path).resolve()
        if STORAGE_DIR.resolve() in target.parents and target.is_file():
            target.unlink()
    except OSError:
        pass


def _cleanup_org(
    org_name: str, emails: list[str], parties: list[str] | None = None
) -> None:
    db = SessionLocal()
    try:
        org = db.query(models.Organization).filter_by(name=org_name).first()
        if org is not None:
            contracts = (
                db.query(models.Contract).filter_by(organization_id=org.id).all()
            )
            for contract in contracts:
                db.query(models.Obligation).filter_by(
                    contract_id=contract.id
                ).delete(synchronize_session=False)
                versions = (
                    db.query(models.DocumentVersion)
                    .filter_by(contract_id=contract.id)
                    .all()
                )
                for version in versions:
                    _unlink_version_file(version.file_path)
                db.query(models.DocumentVersion).filter_by(
                    contract_id=contract.id
                ).delete(synchronize_session=False)
                db.query(models.ContractParty).filter_by(
                    contract_id=contract.id
                ).delete(synchronize_session=False)
                db.delete(contract)
            db.flush()

        for email in emails:
            user = db.query(models.User).filter_by(email=email.lower()).first()
            if user is not None:
                db.query(models.Membership).filter_by(user_id=user.id).delete(
                    synchronize_session=False
                )
                db.delete(user)

        if org is not None:
            db.delete(org)

        for name in parties or []:
            party = db.query(models.Party).filter_by(name=name).first()
            if party is None:
                continue
            still_linked = (
                db.query(models.ContractParty).filter_by(party_id=party.id).count()
            )
            if still_linked == 0:
                db.delete(party)

        db.commit()
    finally:
        db.close()


def _create_contract(token: str, **overrides) -> dict:
    payload = {"title": "Sample Contract", **overrides}
    resp = client.post("/contracts", headers=_headers(token), json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()


# ---- Create ----


def test_analyst_creates_contract_with_parties_and_obligations():
    org = _uid("org")
    email = f"{_uid('analyst')}@example.com"
    party_a, party_b = _uid("party"), _uid("party")
    _signup(email, org, "analyst")
    try:
        token = _login(email)
        resp = client.post(
            "/contracts",
            headers=_headers(token),
            json={
                "title": "Master Services Agreement",
                "source_id": "SRC-001",
                "parties": [party_a, party_b],
                "obligations": [
                    {"description": "Send quarterly report", "due_date": "2026-12-31"},
                    {"description": "Renewal decision"},
                ],
            },
        )
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["title"] == "Master Services Agreement"
        assert body["source_id"] == "SRC-001"
        assert {p["name"] for p in body["parties"]} == {party_a, party_b}
        assert body["obligation_count"] == 2

        by_text = {o["description"]: o for o in body["obligations"]}
        assert by_text["Send quarterly report"]["status"] == "draft"
        assert by_text["Send quarterly report"]["due_date"] == "2026-12-31"
        assert by_text["Renewal decision"]["due_date"] is None
        assert all(o["created_by"] for o in body["obligations"])
        assert all(o["contract_id"] == body["id"] for o in body["obligations"])
    finally:
        _cleanup_org(org, [email], [party_a, party_b])


def test_approver_cannot_create_contract():
    org = _uid("org")
    analyst = f"{_uid('analyst')}@example.com"
    approver = f"{_uid('approver')}@example.com"
    _signup(analyst, org, "analyst")
    _signup(approver, org, "approver")
    try:
        token = _login(approver)
        resp = client.post(
            "/contracts",
            headers=_headers(token),
            json={"title": "Should not be allowed"},
        )
        assert resp.status_code == 403
        assert "Forbidden" in resp.json()["detail"]
    finally:
        _cleanup_org(org, [analyst, approver])


def test_admin_cannot_create_contract():
    org = _uid("org")
    analyst = f"{_uid('analyst')}@example.com"
    admin = f"{_uid('admin')}@example.com"
    _signup(analyst, org, "analyst")
    _make_admin(admin, org)
    try:
        token = _login(admin)
        resp = client.post(
            "/contracts",
            headers=_headers(token),
            json={"title": "Admin writes are out of scope"},
        )
        assert resp.status_code == 403
    finally:
        _cleanup_org(org, [analyst, admin])


def test_create_contract_requires_authentication():
    resp = client.post("/contracts", json={"title": "Anonymous"})
    assert resp.status_code == 401


def test_create_contract_rejects_missing_title():
    org = _uid("org")
    email = f"{_uid('analyst')}@example.com"
    _signup(email, org, "analyst")
    try:
        token = _login(email)
        resp = client.post("/contracts", headers=_headers(token), json={})
        assert resp.status_code == 422
        assert "title" in resp.text
    finally:
        _cleanup_org(org, [email])


def test_create_contract_rejects_whitespace_title():
    org = _uid("org")
    email = f"{_uid('analyst')}@example.com"
    _signup(email, org, "analyst")
    try:
        token = _login(email)
        resp = client.post(
            "/contracts", headers=_headers(token), json={"title": "   "}
        )
        assert resp.status_code == 422
        assert "title must not be empty" in resp.text
    finally:
        _cleanup_org(org, [email])


def test_create_contract_rejects_invalid_due_date():
    org = _uid("org")
    email = f"{_uid('analyst')}@example.com"
    _signup(email, org, "analyst")
    try:
        token = _login(email)
        resp = client.post(
            "/contracts",
            headers=_headers(token),
            json={
                "title": "Bad date contract",
                "obligations": [
                    {"description": "Something", "due_date": "not-a-date"}
                ],
            },
        )
        assert resp.status_code == 422
        assert "due_date" in resp.text
    finally:
        _cleanup_org(org, [email])


def test_create_contract_rejects_empty_party_name():
    org = _uid("org")
    email = f"{_uid('analyst')}@example.com"
    _signup(email, org, "analyst")
    try:
        token = _login(email)
        resp = client.post(
            "/contracts",
            headers=_headers(token),
            json={"title": "Empty party", "parties": [""]},
        )
        assert resp.status_code == 422
        assert "party names must not be empty" in resp.text
    finally:
        _cleanup_org(org, [email])


def test_duplicate_source_id_conflict():
    org = _uid("org")
    email = f"{_uid('analyst')}@example.com"
    _signup(email, org, "analyst")
    try:
        token = _login(email)
        _create_contract(token, title="First", source_id="DUP-001")
        resp = client.post(
            "/contracts",
            headers=_headers(token),
            json={"title": "Second", "source_id": "DUP-001"},
        )
        assert resp.status_code == 409
        assert "source_id" in resp.json()["detail"]
    finally:
        _cleanup_org(org, [email])


# ---- Read ----


def test_analyst_and_approver_can_list_and_read_detail():
    org = _uid("org")
    analyst = f"{_uid('analyst')}@example.com"
    approver = f"{_uid('approver')}@example.com"
    party_name = _uid("party")
    _signup(analyst, org, "analyst")
    _signup(approver, org, "approver")
    try:
        analyst_token = _login(analyst)
        approver_token = _login(approver)
        created = _create_contract(
            analyst_token,
            title="Readable Contract",
            parties=[party_name],
            obligations=[{"description": "Do the thing", "due_date": "2026-11-01"}],
        )

        for token in (analyst_token, approver_token):
            resp = client.get("/contracts", headers=_headers(token))
            assert resp.status_code == 200, resp.text
            ids = [c["id"] for c in resp.json()]
            assert created["id"] in ids

            detail = client.get(
                f"/contracts/{created['id']}", headers=_headers(token)
            )
            assert detail.status_code == 200, detail.text
            body = detail.json()
            assert body["title"] == "Readable Contract"
            assert body["parties"][0]["name"] == party_name
            assert body["obligation_count"] == 1
            assert body["obligations"][0]["description"] == "Do the thing"
    finally:
        _cleanup_org(org, [analyst, approver], [party_name])


def test_contract_detail_unknown_id_404():
    org = _uid("org")
    email = f"{_uid('analyst')}@example.com"
    _signup(email, org, "analyst")
    try:
        token = _login(email)
        resp = client.get("/contracts/999999999", headers=_headers(token))
        assert resp.status_code == 404
        assert resp.json()["detail"] == "Contract not found"
    finally:
        _cleanup_org(org, [email])


def test_unauthenticated_reads_401():
    resp = client.get("/contracts")
    assert resp.status_code == 401


def test_org_isolation_hides_other_orgs_contracts():
    org_a = _uid("org")
    org_b = _uid("org")
    analyst_a = f"{_uid('analyst')}@example.com"
    analyst_b = f"{_uid('analyst')}@example.com"
    _signup(analyst_a, org_a, "analyst")
    _signup(analyst_b, org_b, "analyst")
    try:
        token_a = _login(analyst_a)
        token_b = _login(analyst_b)
        created = _create_contract(token_a, title="Org A secret")

        resp = client.get("/contracts", headers=_headers(token_b))
        assert resp.status_code == 200
        assert created["id"] not in [c["id"] for c in resp.json()]

        resp = client.get(f"/contracts/{created['id']}", headers=_headers(token_b))
        assert resp.status_code == 404
    finally:
        _cleanup_org(org_a, [analyst_a])
        _cleanup_org(org_b, [analyst_b])


# ---- Add party / obligation ----


def test_analyst_adds_obligation():
    org = _uid("org")
    email = f"{_uid('analyst')}@example.com"
    _signup(email, org, "analyst")
    try:
        token = _login(email)
        contract = _create_contract(token)
        resp = client.post(
            f"/contracts/{contract['id']}/obligations",
            headers=_headers(token),
            json={"description": "Manual follow-up", "due_date": "2027-01-15"},
        )
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["contract_id"] == contract["id"]
        assert body["status"] == "draft"
        assert body["due_date"] == "2027-01-15"
        assert body["description"] == "Manual follow-up"
    finally:
        _cleanup_org(org, [email])


def test_approver_cannot_add_obligation():
    org = _uid("org")
    analyst = f"{_uid('analyst')}@example.com"
    approver = f"{_uid('approver')}@example.com"
    _signup(analyst, org, "analyst")
    _signup(approver, org, "approver")
    try:
        contract = _create_contract(_login(analyst))
        resp = client.post(
            f"/contracts/{contract['id']}/obligations",
            headers=_headers(_login(approver)),
            json={"description": "Nope"},
        )
        assert resp.status_code == 403
    finally:
        _cleanup_org(org, [analyst, approver])


def test_add_obligation_unknown_contract_404():
    org = _uid("org")
    email = f"{_uid('analyst')}@example.com"
    _signup(email, org, "analyst")
    try:
        token = _login(email)
        resp = client.post(
            "/contracts/999999999/obligations",
            headers=_headers(token),
            json={"description": "Ghost obligation"},
        )
        assert resp.status_code == 404
        assert resp.json()["detail"] == "Contract not found"
    finally:
        _cleanup_org(org, [email])


def test_analyst_adds_party_then_duplicate_409():
    org = _uid("org")
    email = f"{_uid('analyst')}@example.com"
    party_name = _uid("party")
    _signup(email, org, "analyst")
    try:
        token = _login(email)
        contract = _create_contract(token)

        resp = client.post(
            f"/contracts/{contract['id']}/parties",
            headers=_headers(token),
            json={"name": party_name},
        )
        assert resp.status_code == 201, resp.text
        assert resp.json()["name"] == party_name

        resp = client.post(
            f"/contracts/{contract['id']}/parties",
            headers=_headers(token),
            json={"name": party_name},
        )
        assert resp.status_code == 409
        assert "already linked" in resp.json()["detail"]
    finally:
        _cleanup_org(org, [email], [party_name])


def test_approver_cannot_add_party():
    org = _uid("org")
    analyst = f"{_uid('analyst')}@example.com"
    approver = f"{_uid('approver')}@example.com"
    _signup(analyst, org, "analyst")
    _signup(approver, org, "approver")
    try:
        contract = _create_contract(_login(analyst))
        resp = client.post(
            f"/contracts/{contract['id']}/parties",
            headers=_headers(_login(approver)),
            json={"name": _uid("party")},
        )
        assert resp.status_code == 403
    finally:
        _cleanup_org(org, [analyst, approver])


# ---- Document uploads ----


def _upload(token: str, contract_id: int, filename: str, content: bytes, ctype: str):
    return client.post(
        f"/contracts/{contract_id}/upload",
        headers=_headers(token),
        files={"file": (filename, content, ctype)},
    )


def test_analyst_uploads_file_and_versions_increment():
    org = _uid("org")
    email = f"{_uid('analyst')}@example.com"
    _signup(email, org, "analyst")
    try:
        token = _login(email)
        contract = _create_contract(token)

        resp = _upload(
            token, contract["id"], "agreement.pdf", b"%PDF-1.4 fake", "application/pdf"
        )
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["version_number"] == 1
        assert body["file_name"] == "agreement.pdf"
        assert body["status"] == "uploaded"
        assert "storage" in body["file_path"]
        assert Path(body["file_path"]).is_file(), "file must exist on disk"

        resp = _upload(
            token,
            contract["id"],
            "amendment.docx",
            b"PK fake zip",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
        assert resp.status_code == 201, resp.text
        assert resp.json()["version_number"] == 2

        detail = client.get(f"/contracts/{contract['id']}", headers=_headers(token))
        assert detail.status_code == 200
        versions = detail.json()["document_versions"]
        assert [v["version_number"] for v in versions] == [1, 2]
        assert [v["file_name"] for v in versions] == ["agreement.pdf", "amendment.docx"]
    finally:
        _cleanup_org(org, [email])


def test_upload_rejects_unsupported_file_type():
    org = _uid("org")
    email = f"{_uid('analyst')}@example.com"
    _signup(email, org, "analyst")
    try:
        token = _login(email)
        contract = _create_contract(token)
        resp = _upload(token, contract["id"], "notes.txt", b"plain text", "text/plain")
        assert resp.status_code == 400
        assert "Unsupported file type" in resp.json()["detail"]
    finally:
        _cleanup_org(org, [email])


def test_upload_missing_file_400():
    org = _uid("org")
    email = f"{_uid('analyst')}@example.com"
    _signup(email, org, "analyst")
    try:
        token = _login(email)
        contract = _create_contract(token)
        resp = client.post(
            f"/contracts/{contract['id']}/upload", headers=_headers(token)
        )
        assert resp.status_code == 400
        assert "No file provided" in resp.json()["detail"]
    finally:
        _cleanup_org(org, [email])


def test_upload_rejects_empty_file():
    org = _uid("org")
    email = f"{_uid('analyst')}@example.com"
    _signup(email, org, "analyst")
    try:
        token = _login(email)
        contract = _create_contract(token)
        resp = _upload(token, contract["id"], "empty.pdf", b"", "application/pdf")
        assert resp.status_code == 400
        assert "empty" in resp.json()["detail"].lower()
    finally:
        _cleanup_org(org, [email])


def test_approver_cannot_upload():
    org = _uid("org")
    analyst = f"{_uid('analyst')}@example.com"
    approver = f"{_uid('approver')}@example.com"
    _signup(analyst, org, "analyst")
    _signup(approver, org, "approver")
    try:
        contract = _create_contract(_login(analyst))
        resp = _upload(
            _login(approver), contract["id"], "doc.pdf", b"%PDF", "application/pdf"
        )
        assert resp.status_code == 403
    finally:
        _cleanup_org(org, [analyst, approver])


def test_upload_unknown_contract_404():
    org = _uid("org")
    email = f"{_uid('analyst')}@example.com"
    _signup(email, org, "analyst")
    try:
        token = _login(email)
        resp = _upload(token, 999999999, "doc.pdf", b"%PDF", "application/pdf")
        assert resp.status_code == 404
        assert resp.json()["detail"] == "Contract not found"
    finally:
        _cleanup_org(org, [email])


def test_upload_requires_authentication():
    org = _uid("org")
    email = f"{_uid('analyst')}@example.com"
    _signup(email, org, "analyst")
    try:
        contract = _create_contract(_login(email))
        resp = client.post(
            f"/contracts/{contract['id']}/upload",
            files={"file": ("doc.pdf", b"%PDF", "application/pdf")},
        )
        assert resp.status_code == 401
    finally:
        _cleanup_org(org, [email])
