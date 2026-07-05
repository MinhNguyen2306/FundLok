from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.lending.models import Document

KYC_PURPOSES = ("KYC_ID", "KYC_ADDRESS", "KYC_BUSINESS_REG")


async def project_has_verified_kyc(db: AsyncSession, project_id: UUID) -> bool:
    for purpose in KYC_PURPOSES:
        result = await db.execute(
            select(Document).where(
                Document.entity_type == "PROJECT",
                Document.entity_id == project_id,
                Document.purpose == purpose,
                Document.status == "APPROVED",
            )
        )
        if result.scalar_one_or_none() is None:
            return False
    return True
