from sqlalchemy import (
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import relationship

from .database import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("email", name="uq_users_email"),
    )

    id = Column(Integer, primary_key=True)
    email = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    memberships = relationship("Membership", back_populates="user")


class Organization(Base):
    __tablename__ = "organizations"
    __table_args__ = (
        UniqueConstraint("name", name="uq_organizations_name"),
    )

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    memberships = relationship("Membership", back_populates="organization")


class Membership(Base):
    __tablename__ = "memberships"
    __table_args__ = (
        CheckConstraint(
            "role IN ('analyst', 'approver', 'admin')",
            name="ck_memberships_role_valid",
        ),
        UniqueConstraint(
            "user_id", "organization_id", name="uq_memberships_user_organization"
        ),
    )

    id = Column(Integer, primary_key=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", name="fk_memberships_user_id_users"),
        nullable=False,
    )
    organization_id = Column(
        Integer,
        ForeignKey(
            "organizations.id", name="fk_memberships_organization_id_organizations"
        ),
        nullable=False,
    )
    role = Column(String(20), nullable=False)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user = relationship("User", back_populates="memberships")
    organization = relationship("Organization", back_populates="memberships")


class Contract(Base):
    __tablename__ = "contracts"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "source_id",
            name="uq_contracts_organization_source_id",
        ),
    )

    id = Column(Integer, primary_key=True)
    organization_id = Column(
        Integer,
        ForeignKey(
            "organizations.id", name="fk_contracts_organization_id_organizations"
        ),
        nullable=False,
    )
    title = Column(String(500), nullable=False)
    source_id = Column(String(255), nullable=True)
    created_by = Column(
        Integer,
        ForeignKey("users.id", name="fk_contracts_created_by_users"),
        nullable=False,
    )
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    organization = relationship("Organization")
    creator = relationship("User")
    contract_parties = relationship("ContractParty", back_populates="contract")
    obligations = relationship("Obligation", back_populates="contract")


class Party(Base):
    __tablename__ = "parties"

    id = Column(Integer, primary_key=True)
    name = Column(String(500), nullable=False)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    contract_parties = relationship("ContractParty", back_populates="party")


class ContractParty(Base):
    __tablename__ = "contract_parties"

    contract_id = Column(
        Integer,
        ForeignKey("contracts.id", name="fk_contract_parties_contract_id_contracts"),
        primary_key=True,
    )
    party_id = Column(
        Integer,
        ForeignKey("parties.id", name="fk_contract_parties_party_id_parties"),
        primary_key=True,
    )

    contract = relationship("Contract", back_populates="contract_parties")
    party = relationship("Party", back_populates="contract_parties")


class DocumentVersion(Base):
    __tablename__ = "document_versions"
    __table_args__ = (
        UniqueConstraint(
            "contract_id",
            "version_number",
            name="uq_document_versions_contract_version",
        ),
        CheckConstraint(
            "version_number >= 1",
            name="ck_document_versions_version_number_positive",
        ),
    )

    id = Column(Integer, primary_key=True)
    contract_id = Column(
        Integer,
        ForeignKey(
            "contracts.id", name="fk_document_versions_contract_id_contracts"
        ),
        nullable=False,
    )
    version_number = Column(Integer, nullable=False)
    file_name = Column(String(500), nullable=False)
    file_path = Column(String(1000), nullable=False)
    status = Column(String(20), nullable=False, server_default="uploaded")
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    contract = relationship("Contract")


class Obligation(Base):
    __tablename__ = "obligations"
    __table_args__ = (
        CheckConstraint(
            "status IN ('draft', 'approved', 'rejected')",
            name="ck_obligations_status_valid",
        ),
    )

    id = Column(Integer, primary_key=True)
    contract_id = Column(
        Integer,
        ForeignKey("contracts.id", name="fk_obligations_contract_id_contracts"),
        nullable=False,
    )
    document_version_id = Column(
        Integer,
        ForeignKey(
            "document_versions.id",
            name="fk_obligations_document_version_id_document_versions",
        ),
        nullable=True,
    )
    description = Column(Text, nullable=False)
    due_date = Column(Date, nullable=True)
    status = Column(String(20), nullable=False, server_default="draft")
    created_by = Column(
        Integer,
        ForeignKey("users.id", name="fk_obligations_created_by_users"),
        nullable=False,
    )
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    contract = relationship("Contract", back_populates="obligations")
    document_version = relationship("DocumentVersion")
    creator = relationship("User")


class Approval(Base):
    __tablename__ = "approvals"
    __table_args__ = (
        CheckConstraint(
            "action IN ('confirm', 'correct', 'reject')",
            name="ck_approvals_action_valid",
        ),
    )

    id = Column(Integer, primary_key=True)
    obligation_id = Column(
        Integer,
        ForeignKey(
            "obligations.id", name="fk_approvals_obligation_id_obligations"
        ),
        nullable=False,
    )
    approver_id = Column(
        Integer,
        ForeignKey("users.id", name="fk_approvals_approver_id_users"),
        nullable=False,
    )
    action = Column(String(20), nullable=False)
    comment = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    obligation = relationship("Obligation")
    approver = relationship("User")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", name="fk_audit_logs_user_id_users"),
        nullable=True,
    )
    action = Column(String(100), nullable=False)
    entity_type = Column(String(100), nullable=False)
    entity_id = Column(Integer, nullable=True)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user = relationship("User")
