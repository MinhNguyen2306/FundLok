from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import exists, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.banking.models import ACCOUNT_TYPES, LinkedAccount


def _mask(account_number: str) -> str:
    tail = account_number[-4:] if len(account_number) >= 4 else account_number
    return f"**** {tail}"


async def link_account(
    db: AsyncSession,
    *,
    user_id: UUID,
    account_type: str,
    account_number: str,
    provider: str | None,
    display_name: str | None,
) -> LinkedAccount:
    if account_type not in ACCOUNT_TYPES:
        raise HTTPException(status_code=400, detail=f"account_type must be one of {ACCOUNT_TYPES}")
    if not account_number.strip():
        raise HTTPException(status_code=400, detail="account_number must not be blank")

    account = LinkedAccount(
        user_id=user_id,
        account_type=account_type,
        provider=provider or "MOCK",
        account_ref_masked=_mask(account_number.strip()),
        display_name=display_name,
        status="ACTIVE",
    )
    db.add(account)
    await db.flush()
    await db.refresh(account)
    return account


async def list_accounts(db: AsyncSession, *, user_id: UUID) -> list[LinkedAccount]:
    result = await db.execute(
        select(LinkedAccount)
        .where(LinkedAccount.user_id == user_id)
        .order_by(LinkedAccount.created_at.desc())
    )
    return list(result.scalars().all())


async def has_active_linked_account(db: AsyncSession, *, user_id: UUID) -> bool:
    """docs/specs/banking/account-linking-mock.md section 10 -- the
    precondition `app/market/service.py::place_order` checks before
    accepting an investor's order."""
    result = await db.execute(
        select(exists().where(LinkedAccount.user_id == user_id, LinkedAccount.status == "ACTIVE"))
    )
    return bool(result.scalar())


async def unlink_account(db: AsyncSession, *, user_id: UUID, account_id: UUID) -> LinkedAccount:
    result = await db.execute(
        select(LinkedAccount).where(LinkedAccount.id == account_id, LinkedAccount.user_id == user_id)
    )
    account = result.scalar_one_or_none()
    if account is None:
        raise HTTPException(status_code=404, detail="Linked account not found")
    if account.status != "REVOKED":
        account.status = "REVOKED"
        db.add(account)
        await db.flush()
        await db.refresh(account)
    return account
