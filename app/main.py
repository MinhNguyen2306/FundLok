# main.py
import app.models  # noqa: F401 — register ORM mappers before routes
import os
import uvicorn

from fastapi import FastAPI, Depends, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware # Added for CORS support
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.admin.router import router as admin_router
from app.banking.router import router as banking_router
from app.system.service import is_maintenance_active
from app.system.router import router as system_router
from app.auth.router import router as auth_router
from app.contracts.router import router as contracts_router
from app.core.database import get_db
from app.lending.router import router as lending_router
from app.loans.router import router as loans_router
from app.market.router import router as market_router
from app.oauth.router import router as oauth_router
from app.payments.router import router as payments_router
from app.projects.router import router as projects_router
from app.sme.router import router as sme_router
from app.underwriting.router import router as underwriting_router
from app.uploads.router import files_router, router as uploads_router
from app.users.router import router as users_router
from app.verification.router import kyb_router, kyc_router
from app.gverify.router import kyb_router as gverify_kyb_router, router as gverify_router
from app.contact.router import router as contact_router

app = FastAPI(
    title="FundLok API",
    description="MVP backend for FundLok fintech platform",
    version="0.1.0",
)


# ================= MAINTENANCE MODE =================
# When maintenance is enabled, normal traffic gets a 503. Auth and admin
# routes stay open so a (system) admin can log in and turn it back off.
# Registered BEFORE CORS so CORS stays outermost and the 503 keeps its
# Access-Control headers (otherwise the browser can't read the response).
MAINTENANCE_ALLOW_PREFIXES = (
    "/auth",
    "/admin",
    "/system",  # public maintenance-status read must stay reachable
    "/kyc/webhook",  # Didit verification callbacks must keep arriving
    "/health",
    "/test-db",
    "/docs",
    "/redoc",
    "/openapi.json",
)


@app.middleware("http")
async def maintenance_gate(request: Request, call_next):
    if request.method == "OPTIONS" or request.url.path.startswith(MAINTENANCE_ALLOW_PREFIXES):
        return await call_next(request)
    enabled, message = await is_maintenance_active()
    if enabled:
        return JSONResponse(
            status_code=503,
            content={"detail": message or "The service is temporarily down for maintenance."},
        )
    return await call_next(request)
# =====================================================


# ================= CORS CONFIGURATION =================
# Define the URLs allowed to access this API[cite: 5]
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://fundlok-front-end.vercel.app"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Permits OPTIONS, POST, etc.
    allow_headers=["*"],
)
# =====================================================

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.get("/test-db")
async def test_db(db: AsyncSession = Depends(get_db)):
    result = (await db.execute(text("SELECT 1"))).scalar()
    return {"db_connected": result == 1}


# Include routers
app.include_router(auth_router)
app.include_router(oauth_router)
app.include_router(users_router)
app.include_router(projects_router)
app.include_router(sme_router)
app.include_router(files_router)
app.include_router(kyc_router)
app.include_router(kyb_router)
app.include_router(gverify_router)
app.include_router(gverify_kyb_router)
app.include_router(loans_router)
app.include_router(lending_router)
app.include_router(underwriting_router)
app.include_router(uploads_router)
app.include_router(contracts_router)
app.include_router(market_router)
app.include_router(payments_router)
app.include_router(banking_router)
app.include_router(admin_router)
app.include_router(system_router)
app.include_router(contact_router)

if __name__ == "__main__":
    # Get the port from Cloud Run environment (default to 8080 if not set)
    # If running locally, it will use port 8000
    port = int(os.environ.get("PORT", 8080))
    
    # Run the application
    # host="0.0.0.0" allows the server to accept connections from outside the container
    uvicorn.run("app.main:app", host="0.0.0.0", port=port)