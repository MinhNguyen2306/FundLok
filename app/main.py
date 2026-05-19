# main.py
import app.models  # noqa: F401 — register ORM mappers before routes
import os
import uvicorn

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware # Added for CORS support
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


# ================= CORS CONFIGURATION =================
# Define the URLs allowed to access this API[cite: 5]
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
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
def test_db(db: Session = Depends(get_db)):
    result = db.execute(text("SELECT 1")).scalar()
    return {"db_connected": result == 1}

# Include routers
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

if __name__ == "__main__":
    # Get the port from Cloud Run environment (default to 8080 if not set)
    # If running locally, it will use port 8000
    port = int(os.environ.get("PORT", 8000))
    
    # Run the application
    # host="0.0.0.0" allows the server to accept connections from outside the container
    uvicorn.run("main:app", host="0.0.0.0", port=port)