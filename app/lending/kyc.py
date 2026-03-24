from uuid import UUID

from sqlalchemy.orm import Session

from app.lending.models import Document

KYC_PURPOSES = ("KYC_ID", "KYC_ADDRESS", "KYC_BUSINESS_REG")


def project_has_verified_kyc(db: Session, project_id: UUID) -> bool:
    for purpose in KYC_PURPOSES:
        row = (
            db.query(Document)
            .filter(
                Document.entity_type == "PROJECT",
                Document.entity_id == project_id,
                Document.purpose == purpose,
                Document.status == "APPROVED",
            )
            .first()
        )
        if row is None:
            return False
    return True
