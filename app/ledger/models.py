"""Double-entry ledger foundation ORM models (app/ledger/).

Spec: docs/specs/ledger/ledger-foundation.md (ACCEPTED v1.0)
ADRs: docs/adr/002-omnibus-brankas-architecture.md,
      docs/adr/003-omnibus-first-escrow-compatible-ledger.md

`LedgerEntry` used to live in app/lending/models.py as a flat, single-entry
movement log (no account references, no notion of from -> to). This module
evolves it into the postings table of a double-entry system and introduces
the account layer ADR-003 requires:

    custodial_accounts   -- one physical bank account (PLATFORM=omnibus today,
                             CONTRACT=future per-contract escrow)
    ledger_accounts      -- the internal chart of accounts, each tied to a
                             custodial_account
    ledger_transactions  -- the idempotent event header
    ledger_entries       -- postings ("legs"); each row moves `amount` from
                             debit_account_id to credit_account_id

`app/lending/models.py` re-exports `LedgerEntry` from here (see the comment
there) so existing imports (`from app.lending.models import LedgerEntry`)
keep working; `Contract.ledger_entries` still resolves it by class name via
the shared SQLAlchemy registry.
"""
import uuid

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.base import Base


class CustodialAccount(Base):
    """One physical bank account (ADR-003).

    scope='PLATFORM' -- the single pooled omnibus account. Exactly one row
        (enforced by the partial unique index below), contract_id NULL.
    scope='CONTRACT' -- a future per-contract escrow account. One row per
        contract, contract_id NOT NULL. Dormant under omnibus; the seam
        that makes an omnibus -> escrow pivot a migration, not a rewrite.
    """

    __tablename__ = "custodial_accounts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scope = Column(Text, nullable=False)
    contract_id = Column(UUID(as_uuid=True), ForeignKey("contracts.id", ondelete="RESTRICT"), nullable=True)
    bank_account_ref = Column(Text, nullable=True)
    status = Column(Text, nullable=False, server_default="ACTIVE")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    ledger_accounts = relationship("LedgerAccount", back_populates="custodial_account")

    __table_args__ = (
        # Partial unique indexes -- declared here (in addition to being
        # created by the migration) so `alembic check` sees the model and
        # the DB agree; see the migration for the actual DDL/rationale.
        Index(
            "uq_single_platform_custodial",
            "scope",
            unique=True,
            postgresql_where=text("scope = 'PLATFORM'"),
        ),
        Index(
            "uq_custodial_accounts_contract_id",
            "contract_id",
            unique=True,
            postgresql_where=text("scope = 'CONTRACT'"),
        ),
    )


class LedgerAccount(Base):
    """The internal chart of accounts. Every account belongs to exactly one
    custodial_account (ADR-003 indirection -- never assume a global pool).

    account_type:
      OMNIBUS_CASH -- the platform's pooled cash position. Platform-level:
                       owner_user_id and contract_id are both NULL.
      LENDER       -- one investor's position within one contract.
      BORROWER     -- one SME's position within one contract.
      FL_REVENUE   -- FL's fee revenue. Platform-level.
      SUSPENSE     -- provisioned type/shape only (spec Open Q#2). No
                       handling/sweep logic is built against it yet.
    """

    __tablename__ = "ledger_accounts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_type = Column(Text, nullable=False)
    custodial_account_id = Column(
        UUID(as_uuid=True), ForeignKey("custodial_accounts.id", ondelete="RESTRICT"), nullable=False
    )
    owner_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    contract_id = Column(UUID(as_uuid=True), ForeignKey("contracts.id", ondelete="RESTRICT"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    custodial_account = relationship("CustodialAccount", back_populates="ledger_accounts")

    __table_args__ = (
        UniqueConstraint(
            "account_type",
            "custodial_account_id",
            "owner_user_id",
            "contract_id",
            name="uq_ledger_accounts_role_party_contract",
        ),
    )


class LedgerTransaction(Base):
    """The idempotent event header. One economic event (e.g. one repayment
    that splits into N lender distributions + a fee) = one row here, with
    >=2 `ledger_entries` rows ("legs") sharing this id.
    """

    __tablename__ = "ledger_transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_type = Column(Text, nullable=False)
    contract_id = Column(UUID(as_uuid=True), ForeignKey("contracts.id", ondelete="RESTRICT"), nullable=True)
    idempotency_key = Column(Text, unique=True, nullable=True)
    reference = Column(Text, nullable=True)
    occurred_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    entries = relationship("LedgerEntry", back_populates="ledger_transaction")


class LedgerEntry(Base):
    """A posting ("leg"): moves `amount` from debit_account_id to
    credit_account_id. Append-only at the app layer (no UPDATE/DELETE here
    or anywhere) and at the DB layer (BEFORE UPDATE/DELETE trigger, see the
    migration). Corrections are new, reversing transactions -- never a
    mutation of an existing row.
    """

    __tablename__ = "ledger_entries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contract_id = Column(UUID(as_uuid=True), ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False)
    ledger_transaction_id = Column(
        UUID(as_uuid=True), ForeignKey("ledger_transactions.id", ondelete="RESTRICT"), nullable=False
    )
    debit_account_id = Column(UUID(as_uuid=True), ForeignKey("ledger_accounts.id", ondelete="RESTRICT"), nullable=False)
    credit_account_id = Column(UUID(as_uuid=True), ForeignKey("ledger_accounts.id", ondelete="RESTRICT"), nullable=False)
    type = Column(Text, nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    reference = Column(Text)
    occurred_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))

    contract = relationship("Contract", back_populates="ledger_entries")
    ledger_transaction = relationship("LedgerTransaction", back_populates="entries")
    debit_account = relationship("LedgerAccount", foreign_keys=[debit_account_id])
    credit_account = relationship("LedgerAccount", foreign_keys=[credit_account_id])
