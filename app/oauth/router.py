from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.oauth.schema import OAuthLoginRequest, OAuthTokenResponse
from app.oauth.service import OAuthService


router = APIRouter(prefix="/auth/oauth", tags=["oauth"])


@router.post("/login", response_model=OAuthTokenResponse)
async def oauth_login(body: OAuthLoginRequest, response: Response, db: AsyncSession = Depends(get_db)):
    tokens = await OAuthService(db).login(body.provider, body.token)

    response.set_cookie(key="access_token", value=tokens["access_token"], httponly=True, samesite="lax", secure=False, max_age=30 * 60)
    response.set_cookie(key="refresh_token", value=tokens["refresh_token"], httponly=True, samesite="lax", secure=False, max_age=14 * 24 * 60 * 60)

    return tokens
