from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.lending.models import LoanApplication, Project
from app.loans.lite_grading import LiteBand, LiteGradingError, grade_lite
from app.loans.schemas import LoanApplicationCreate, LoanApplicationFiguresIn
from app.projects.service import user_owns_project
from app.users.models import Role, User
from uuid import UUID


async def create_application(db: AsyncSession, body: LoanApplicationCreate, current_user: User) -> LoanApplication:
    if current_user.role != Role.SME.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only SMEs can create applications")
    if not await user_owns_project(db, current_user.id, body.business_id):
        raise HTTPException(status_code=403, detail="Business does not belong to this user")
    app_row = LoanApplication(
        project_id=body.business_id,
        requested_amount=body.requested_amount,
        duration_months=body.duration_months,
        purpose=body.purpose,
        repayment_preference=body.repayment_preference,
        status="DRAFT",
    )
    db.add(app_row)
    await db.flush()
    await db.refresh(app_row)
    return app_row


async def _owned_application(
    db: AsyncSession, application_id: UUID, current_user: User
) -> LoanApplication:
    """Load an application the caller is actually allowed to touch.

    404 rather than 403 when the application exists but belongs to someone
    else: telling a stranger "this exists but is not yours" confirms which
    application ids are real, which is an enumeration oracle over other SMEs'
    borrowing.
    """
    result = await db.execute(select(LoanApplication).where(LoanApplication.id == application_id))
    row = result.scalar_one_or_none()
    if not row or not await user_owns_project(db, current_user.id, row.project_id):
        raise HTTPException(status_code=404, detail="Application not found")
    return row


async def save_figures(
    db: AsyncSession,
    application_id: UUID,
    body: LoanApplicationFiguresIn,
    current_user: User,
) -> LoanApplication:
    """Replace the self-reported figures on a draft application.

    A full replace, not a merge: the wizard always sends the complete set, and
    merging would let a second request that omitted a field silently keep a
    stale value the applicant believed they had cleared.
    """
    if current_user.role != Role.SME.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only SMEs can save figures")

    row = await _owned_application(db, application_id, current_user)

    # Figures are underwriting inputs. Once the application is submitted they
    # are evidence of what was claimed, so they freeze with it -- otherwise an
    # applicant could restate their revenue after seeing the offer.
    if row.status != "DRAFT":
        raise HTTPException(status_code=400, detail="Application is not in DRAFT status")

    row.self_reported_figures = body.model_dump()
    row.figures_updated_at = datetime.now(timezone.utc)
    db.add(row)
    await db.flush()
    await db.refresh(row)
    return row


def _reason(code: str, message: str, fields: list[str] | None = None) -> dict:
    """A 409 body the frontend can translate.

    `code` is the contract; `message` is a fallback for anything that cannot
    translate it (logs, API consumers, a frontend that has no string for a code
    added after it shipped).
    """
    body = {"code": code, "message": message}
    if fields:
        body["fields"] = fields
    return body


def _operating_months(incorporation_date: date | None, today: date) -> int:
    """Whole months between incorporation and today.

    Calendar months, not days/30: the engine compares this against
    `duration_months` (soft gate 2, `history_vs_term`) and against the
    operating-history band, both of which are stated in months. A day-based
    approximation drifts by up to a fortnight a year and can flip a borderline
    gate, which is not a thing an applicant could ever explain.
    """
    if incorporation_date is None:
        raise LiteGradingError(
            "This business has no incorporation date on file, so its operating "
            "history cannot be established.",
            code="NO_INCORPORATION_DATE",
        )
    if incorporation_date > today:
        raise LiteGradingError(
            "Incorporation date is in the future.",
            code="FUTURE_INCORPORATION_DATE",
        )
    months = (today.year - incorporation_date.year) * 12 + (
        today.month - incorporation_date.month
    )
    # Not yet past the day-of-month anniversary, so the final month is partial.
    if today.day < incorporation_date.day:
        months -= 1
    return max(months, 0)


async def indicative_rate(
    db: AsyncSession, application_id: UUID, current_user: User
) -> LiteBand:
    """The indicative interest band for an application's stated figures.

    Read-only and computed on demand rather than stored. The band is not an
    offer and nothing is agreed against it -- it is a preview of what the
    engine makes of the numbers the applicant just typed, and it changes the
    moment they change a figure. Persisting it would create a second source of
    truth for a rate that the real, post-KYC score run supersedes anyway. The
    response is still stamped with `engine_version`/`params_version` so a band
    a user was shown can be reconstructed from the stored figures.

    Every failure here is a 409 with the reason: the applicant is mid-wizard
    and the fix is always another field, so "what is missing" is the whole
    useful content of the error.

    Those 409s carry a STRUCTURED detail -- `{code, message, fields}` -- rather
    than the bare string the rest of the API uses. A deliberate exception to
    that convention: this is the one endpoint whose errors are rendered to an
    applicant in two languages, and a prose string can only ever be shown in the
    language the server wrote it in. `message` stays as the English fallback and
    the log line; `code` is what the frontend translates; `fields` are machine
    names so the UI can label them in the reader's language.
    """
    row = await _owned_application(db, application_id, current_user)

    if not row.self_reported_figures:
        raise HTTPException(
            status_code=409,
            detail=_reason(
                "NO_FIGURES",
                "No figures have been saved for this application yet.",
            ),
        )

    project = await db.get(Project, row.project_id)
    if project is None:
        # The FK is ON DELETE CASCADE, so a live application always has one.
        raise HTTPException(status_code=404, detail="Application not found")

    # Machine names, not prose: the UI labels them in the applicant's language.
    missing = [
        name
        for name, value in (
            ("industry", project.industry),
            ("employee_count", project.employee_count),
            ("duration_months", row.duration_months),
        )
        if value is None
    ]
    if missing:
        raise HTTPException(
            status_code=409,
            detail=_reason(
                "MISSING_INPUTS",
                (
                    "This application is missing "
                    f"{', '.join(missing)}, which the grading engine requires."
                ),
                fields=missing,
            ),
        )

    try:
        return grade_lite(
            # `company_code` is a label on GradingInput -- no grading module
            # reads it -- so the project id stands in when a tax id has not
            # been captured. It must not silently become an empty string: the
            # value is echoed into score-run records for traceability.
            company_code=project.tax_id or str(project.id),
            industry=project.industry,
            employee_count=project.employee_count,
            incorporation_date_months=_operating_months(
                project.incorporation_date, datetime.now(timezone.utc).date()
            ),
            loan_size_vnd=Decimal(row.requested_amount),
            duration_months=row.duration_months,
            figures=row.self_reported_figures,
        )
    except LiteGradingError as exc:
        # Written to be shown to an applicant -- costs above revenue, an
        # unscoreable industry, a headcount outside every band. A real answer
        # about their numbers, not a bug.
        raise HTTPException(
            status_code=409, detail=_reason(exc.code, str(exc))
        ) from exc
    except ValueError as exc:
        # `grade()`'s own input validation (core spec §7): loan size outside
        # `loan_constraints`, a term not in `allowed_durations_months`, an
        # unrecognised industry. Those bounds are enforced at create time now,
        # but rows written before that validation existed still fail them, and
        # a legacy application must not 500 an applicant's wizard.
        raise HTTPException(
            status_code=409,
            detail=_reason(
                "OUT_OF_ENGINE_BOUNDS",
                (
                    "This application's amount or term is outside what the "
                    f"grading engine accepts: {exc}"
                ),
            ),
        ) from exc


async def submit_application(db: AsyncSession, application_id: UUID, current_user: User) -> LoanApplication:
    if current_user.role != Role.SME.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only SMEs can submit")
    result = await db.execute(select(LoanApplication).where(LoanApplication.id == application_id))
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Application not found")
    if not await user_owns_project(db, current_user.id, row.project_id):
        raise HTTPException(status_code=403, detail="Not authorized")
    if row.status != "DRAFT":
        raise HTTPException(status_code=400, detail="Application is not in DRAFT status")
    row.status = "SUBMITTED"
    row.submitted_at = datetime.now(timezone.utc)
    db.add(row)
    await db.flush()
    await db.refresh(row)
    return row
