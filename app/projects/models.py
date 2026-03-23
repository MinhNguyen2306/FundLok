"""ORM models for projects live in app.lending.models; re-export for compatibility."""

from app.lending.models import LoanApplication, Project, ProjectOwnership

__all__ = ["Project", "ProjectOwnership", "LoanApplication"]
