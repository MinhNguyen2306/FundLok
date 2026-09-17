"""Service functions for the `documents` entity (app/lending/models.py).

`app/lending/kyc.py` already reads `Document.status` to gate listing
(`project_has_verified_kyc`); this is the write side that was missing
entirely (HANDOFF-03 GAP-1 / Issue 12): nothing anywhere in the codebase
ever sets `Document.status = "APPROVED"`, so no project could ever pass
that check through a real code path.
"""
from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.lending.models import Document
from app.utils.audit import append_audit


async def approve_document(
    db: AsyncSession,
    *,
    document_id: UUID,
    rationale: str,
    actor_id: UUID,
    ip_address: str | None,
) -> Document:
    result = await db.execute(select(Document).where(Document.id == document_id))
    document = result.scalar_one_or_none()
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    if document.status == "APPROVED":
        raise HTTPException(status_code=400, detail="Document is already APPROVED")

    before_state = {"status": document.status}
    now = datetime.now(timezone.utc)
    document.status = "APPROVED"
    document.verified_at = now
    db.add(document)
    await db.flush()
    await db.refresh(document)

    append_audit(
        db,
        entity_type="DOCUMENT",
        entity_id=document.id,
        action="APPROVE",
        actor_id=actor_id,
        before_state=before_state,
        after_state={
            "status": "APPROVED",
            "verified_at": now.isoformat(),
            "rationale": rationale,
        },
        ip_address=ip_address,
    )
    return document
