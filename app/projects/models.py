from sqlalchemy import Column, String, ForeignKey, Enum, JSON
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base
from enum import Enum as PyEnum
import uuid

class ProjectStatus(str, PyEnum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"

class Project(Base):
    __tablename__ = "projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    legal_name = Column(String, nullable=False)
    tax_id = Column(String, unique=True)
    industry = Column(String)
    address = Column(JSON)
    status = Column(Enum(ProjectStatus), default=ProjectStatus.ACTIVE)