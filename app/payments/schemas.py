from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel


class DisbursementCreate(BaseModel):
    contract_id: UUID
    bank_account: str
    amount: Decimal


class DisbursementOut(BaseModel):
    disbursement_id: UUID
    status: str


class RepaymentCreate(BaseModel):
    contract_id: UUID
    amount: Decimal
    paid_at: datetime
    reference: str | None = None


class DistributionOut(BaseModel):
    ledger_entry_id: UUID
    amount: Decimal


class RepaymentOut(BaseModel):
    repayment_id: UUID
    balances: list[DistributionOut]
