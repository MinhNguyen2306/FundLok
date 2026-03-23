import app.models  # noqa: F401 — register ORM mappers before routes

from fastapi import FastAPI, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.admin.router import router as admin_router
from app.auth.router import router as auth_router
from app.contracts.router import router as contracts_router
from app.core.database import get_db
from app.files.router import router as files_router
from app.loans.router import router as loans_router
from app.market.router import router as market_router
from app.payments.router import router as payments_router
from app.projects.router import router as projects_router
from app.sme.router import router as sme_router
from app.underwriting.router import router as underwriting_router
from app.users.router import router as users_router

app = FastAPI(
    title="FundLok API",
    description="MVP backend for FundLok fintech platform",
    version="0.1.0",
)


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.get("/test-db")
def test_db(db: Session = Depends(get_db)):
    result = db.execute(text("SELECT 1")).scalar()
    return {"db_connected": result == 1}


# Include routers **after** app is defined
# temporarily commented out - edwardw 2006/03/09
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(projects_router)
app.include_router(sme_router)
app.include_router(files_router)
app.include_router(loans_router)
app.include_router(underwriting_router)
app.include_router(contracts_router)
app.include_router(market_router)
app.include_router(payments_router)
app.include_router(admin_router)


