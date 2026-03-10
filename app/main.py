from fastapi import FastAPI, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.auth.router import router as auth_router
from app.projects.router import router as projects_router
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
# app.include_router(projects_router)
app.include_router(users_router)


