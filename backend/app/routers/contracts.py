# Contract CRUD with role-based access control.
# Reads: any role (analyst, approver, admin). Writes: analyst only.
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..auth import get_db, require_role
from ..models import Contract, ContractParty, Membership, Obligation, Party, User

router = APIRouter(prefix="/contracts", tags=["contracts"])

READ_ROLES = ("analyst", "approver", "admin")
WRITE_ROLES = ("analyst",)


# ---- Input schemas (validation errors come back as FastAPI 422 detail) ----


class PartyIn(BaseModel):
    name: str = Field(min_length=1, max_length=500)

    @field_validator("name")
    @classmethod
    def _strip_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("party name must not be empty")
        return value


class ObligationIn(BaseModel):
    description: str = Field(min_length=1, max_length=5000)
    due_date: date | None = None

    @field_validator("description")
    @classmethod
    def _strip_description(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("description must not be empty")
        return value


class ContractCreateIn(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    source_id: str | None = Field(default=None, max_length=255)
    parties: list[str] = Field(default_factory=list, max_length=50)
    obligations: list[ObligationIn] = Field(default_factory=list, max_length=50)

    @field_validator("title")
    @classmethod
    def _strip_title(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("title must not be empty")
        return value

    @field_validator("source_id", mode="before")
    @classmethod
    def _empty_source_is_none(cls, value):
        if isinstance(value, str):
            value = value.strip()
            return value or None
        return value

    @field_validator("parties")
    @classmethod
    def _strip_parties(cls, value: list[str]) -> list[str]:
        cleaned = []
        for name in value:
            name = name.strip()
            if not name:
                raise ValueError("party names must not be empty")
            cleaned.append(name)
        # A contract cannot link the same party twice (contract_parties PK).
        return list(dict.fromkeys(cleaned))


# ---- Output schemas ----


class PartyOut(BaseModel):
    id: int
    name: str


class ObligationOut(BaseModel):
    id: int
    contract_id: int
    description: str
    due_date: date | None
    status: str
    document_version_id: int | None
    created_by: int
    created_at: datetime


class ContractListOut(BaseModel):
    id: int
    title: str
    source_id: str | None
    created_at: datetime
    parties: list[PartyOut]
    obligation_count: int


class ContractDetailOut(ContractListOut):
    obligations: list[ObligationOut]


# ---- Helpers ----


def _membership(db: Session, user: User) -> Membership:
    membership = (
        db.query(Membership).filter_by(user_id=user.id).order_by(Membership.id).first()
    )
    if membership is None:
        # require_role already rejects users without a role; belt and braces.
        raise HTTPException(status_code=403, detail="Forbidden for this role")
    return membership


def _find_contract(db: Session, user: User, contract_id: int) -> Contract:
    # Cross-organization access reports 404 so contract ids never leak.
    membership = _membership(db, user)
    contract = (
        db.query(Contract)
        .filter(
            Contract.id == contract_id,
            Contract.organization_id == membership.organization_id,
        )
        .first()
    )
    if contract is None:
        raise HTTPException(status_code=404, detail="Contract not found")
    return contract


def _party_out(party: Party) -> PartyOut:
    return PartyOut(id=party.id, name=party.name)


def _obligation_out(item: Obligation) -> ObligationOut:
    return ObligationOut(
        id=item.id,
        contract_id=item.contract_id,
        description=item.description,
        due_date=item.due_date,
        status=item.status,
        document_version_id=item.document_version_id,
        created_by=item.created_by,
        created_at=item.created_at,
    )


def _parties_of(db: Session, contract_id: int) -> list[PartyOut]:
    links = (
        db.query(ContractParty)
        .filter_by(contract_id=contract_id)
        .join(Party, Party.id == ContractParty.party_id)
        .order_by(Party.name, Party.id)
        .all()
    )
    return [_party_out(link.party) for link in links]


def _detail(db: Session, contract: Contract) -> ContractDetailOut:
    obligations = (
        db.query(Obligation)
        .filter_by(contract_id=contract.id)
        .order_by(Obligation.id)
        .all()
    )
    return ContractDetailOut(
        id=contract.id,
        title=contract.title,
        source_id=contract.source_id,
        created_at=contract.created_at,
        parties=_parties_of(db, contract.id),
        obligation_count=len(obligations),
        obligations=[_obligation_out(item) for item in obligations],
    )


def _list_item(db: Session, contract: Contract) -> ContractListOut:
    count = db.query(Obligation).filter_by(contract_id=contract.id).count()
    return ContractListOut(
        id=contract.id,
        title=contract.title,
        source_id=contract.source_id,
        created_at=contract.created_at,
        parties=_parties_of(db, contract.id),
        obligation_count=count,
    )


# ---- Endpoints ----


@router.post("", response_model=ContractDetailOut, status_code=201)
def create_contract(
    payload: ContractCreateIn,
    user: User = Depends(require_role(*WRITE_ROLES)),
    db: Session = Depends(get_db),
):
    membership = _membership(db, user)

    # Friendly pre-check; the IntegrityError guard below still catches races.
    if payload.source_id is not None:
        existing = (
            db.query(Contract)
            .filter_by(
                organization_id=membership.organization_id,
                source_id=payload.source_id,
            )
            .first()
        )
        if existing is not None:
            raise HTTPException(
                status_code=409,
                detail="source_id is already used by another contract in this organization",
            )

    contract = Contract(
        organization_id=membership.organization_id,
        title=payload.title,
        source_id=payload.source_id,
        created_by=user.id,
    )
    db.add(contract)

    try:
        db.flush()

        for name in payload.parties:
            party = db.query(Party).filter_by(name=name).first()
            if party is None:
                party = Party(name=name)
                db.add(party)
                db.flush()
            db.add(ContractParty(contract_id=contract.id, party_id=party.id))

        for item in payload.obligations:
            db.add(
                Obligation(
                    contract_id=contract.id,
                    description=item.description,
                    due_date=item.due_date,
                    created_by=user.id,
                )
            )

        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="source_id is already used by another contract in this organization",
        )
    db.refresh(contract)
    return _detail(db, contract)


@router.get("", response_model=list[ContractListOut])
def list_contracts(
    user: User = Depends(require_role(*READ_ROLES)),
    db: Session = Depends(get_db),
):
    membership = _membership(db, user)
    contracts = (
        db.query(Contract)
        .filter_by(organization_id=membership.organization_id)
        .order_by(Contract.id.desc())
        .all()
    )
    return [_list_item(db, contract) for contract in contracts]


@router.get("/{contract_id}", response_model=ContractDetailOut)
def get_contract(
    contract_id: int,
    user: User = Depends(require_role(*READ_ROLES)),
    db: Session = Depends(get_db),
):
    return _detail(db, _find_contract(db, user, contract_id))


@router.post("/{contract_id}/parties", response_model=PartyOut, status_code=201)
def add_party(
    contract_id: int,
    payload: PartyIn,
    user: User = Depends(require_role(*WRITE_ROLES)),
    db: Session = Depends(get_db),
):
    contract = _find_contract(db, user, contract_id)
    party = db.query(Party).filter_by(name=payload.name).first()
    if party is None:
        party = Party(name=payload.name)
        db.add(party)
        db.flush()

    already = (
        db.query(ContractParty)
        .filter_by(contract_id=contract.id, party_id=party.id)
        .first()
    )
    if already is not None:
        raise HTTPException(
            status_code=409,
            detail=f"Party '{payload.name}' is already linked to this contract",
        )

    db.add(ContractParty(contract_id=contract.id, party_id=party.id))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=f"Party '{payload.name}' is already linked to this contract",
        )
    db.refresh(party)
    return _party_out(party)


@router.post("/{contract_id}/obligations", response_model=ObligationOut, status_code=201)
def add_obligation(
    contract_id: int,
    payload: ObligationIn,
    user: User = Depends(require_role(*WRITE_ROLES)),
    db: Session = Depends(get_db),
):
    contract = _find_contract(db, user, contract_id)
    obligation = Obligation(
        contract_id=contract.id,
        description=payload.description,
        due_date=payload.due_date,
        created_by=user.id,
    )
    db.add(obligation)
    db.commit()
    db.refresh(obligation)
    return _obligation_out(obligation)
