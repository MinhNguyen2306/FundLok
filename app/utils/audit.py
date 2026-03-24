from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.lending.models import AuditLog


def append_audit(
    db: Session,
    *,
    entity_type: str,
    entity_id: UUID | None,
    action: str,
    actor_id: UUID | None,
    before_state: dict[str, Any] | None = None,
    after_state: dict[str, Any] | None = None,
    ip_address: str | None = None,
) -> None:
    db.add(
        AuditLog(
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            actor_id=actor_id,
            before_state=before_state,
            after_state=after_state,
            ip_address=ip_address,
        )
    )
