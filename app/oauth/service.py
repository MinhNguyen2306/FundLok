from abc import ABC, abstractmethod

import httpx
from fastapi import HTTPException, status
from jose import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.service import create_token_pair
from app.core.config import settings
from app.oauth.schema import OAuthProvider, OAuthUserInfo
from app.users.models import User


class OAuthProviderBase(ABC):
    provider: OAuthProvider
    issuer: str
    discovery_url: str
    client_id: str | None

    def __init__(self, client_id: str | None):
        self.client_id = client_id

    async def login(self, db: AsyncSession, token: str) -> dict:
        claims = self.verify_token(token)
        user_info = self.map_claims(claims)
        user = await self.get_or_create_user(db, user_info)
        tokens = await create_token_pair(db, user.id)
        await db.commit()
        return tokens

    def verify_token(self, token: str) -> dict:
        return self.verify_id_token(token)

    def verify_id_token(self, id_token: str) -> dict:
        if not self.client_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"{self.provider.value} OAuth client ID is not configured",
            )

        try:
            discovery = self._fetch_json(self.discovery_url)
            jwks = self._fetch_json(discovery["jwks_uri"])
            header = jwt.get_unverified_header(id_token)
            key = self._find_key(jwks["keys"], header.get("kid"))
            claims = jwt.decode(
                id_token,
                key,
                algorithms=[header.get("alg", "RS256")],
                audience=self.client_id,
                options={"verify_iss": False},
            )
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid OAuth token",
            ) from exc

        if not self._issuer_is_valid(claims.get("iss")):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid OAuth issuer",
            )

        if claims.get("email_verified") is not True and self.provider == OAuthProvider.GOOGLE:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Google email is not verified",
            )

        return claims

    @abstractmethod
    def map_claims(self, claims: dict) -> OAuthUserInfo:
        raise NotImplementedError

    @abstractmethod
    def _issuer_is_valid(self, issuer: str | None) -> bool:
        raise NotImplementedError

    async def get_or_create_user(self, db: AsyncSession, user_info: OAuthUserInfo) -> User:
        result = await db.execute(select(User).where(User.email == user_info.email))
        user = result.scalar_one_or_none()
        if user:
            # The provider has already confirmed ownership of this email, so an
            # existing account that signed up via email/password should be
            # considered verified once they log in through OAuth.
            if user_info.email_verified and not user.email_verified:
                user.email_verified = True
                await db.flush()
            return user

        user = User(
            email=user_info.email,
            phone=None,
            full_name=user_info.full_name,
            # No password: this account signs in through the provider. The
            # column is nullable (migration d5a8c31f6b02) precisely so this
            # state is representable.
            #
            # It used to hold token_urlsafe(32) -- a random string, not a hash.
            # passlib can't identify that format, so verify_password() raised
            # UnknownHashError instead of returning False: any password-login
            # attempt on an OAuth account was a 500, not a 401. It also made
            # has_password report True, hiding the "Set password" flow from the
            # only users who need it.
            password_hash=None,
            role=None,  # chosen later via /select-role, same as email/password signup
            status="ACTIVE",
            email_verified=True,
        )
        db.add(user)
        await db.flush()
        return user

    def _fetch_json(self, url: str) -> dict:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(url)
            response.raise_for_status()
            return response.json()

    def _find_key(self, keys: list[dict], kid: str | None) -> dict:
        if not kid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="OAuth token header is missing key id",
            )

        for key in keys:
            if key.get("kid") == kid:
                return key

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="OAuth signing key not found",
        )


class GoogleOAuthProvider(OAuthProviderBase):
    provider = OAuthProvider.GOOGLE
    issuer = "https://accounts.google.com"
    discovery_url = "https://accounts.google.com/.well-known/openid-configuration"

    def map_claims(self, claims: dict) -> OAuthUserInfo:
        return OAuthUserInfo(
            provider=self.provider,
            provider_subject=claims["sub"],
            email=claims["email"],
            full_name=claims.get("name"),
            email_verified=bool(claims.get("email_verified")),
        )

    def verify_token(self, token: str) -> dict:
        return self.verify_access_token(token)

    def verify_access_token(self, access_token: str) -> dict:
        url = "https://www.googleapis.com/oauth2/v3/userinfo"

        with httpx.Client(timeout=10.0) as client:
            response = client.get(url, headers={"Authorization": f"Bearer {access_token}"})

        if response.status_code != 200:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Google access token")

        claims = response.json()
        if not claims.get("sub") or not claims.get("email"):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Google access token payload")

        return claims

    def _issuer_is_valid(self, issuer: str | None) -> bool:
        return issuer in {"https://accounts.google.com", "accounts.google.com"}


class MicrosoftOAuthProvider(OAuthProviderBase):
    provider = OAuthProvider.MICROSOFT

    @property
    def discovery_url(self) -> str:
        return f"https://login.microsoftonline.com/{settings.MICROSOFT_TENANT_ID}/v2.0/.well-known/openid-configuration"

    def map_claims(self, claims: dict) -> OAuthUserInfo:
        return OAuthUserInfo(
            provider=self.provider,
            provider_subject=claims["sub"],
            email=claims.get("preferred_username") or claims["email"],
            full_name=claims.get("name"),
            email_verified=True,
        )

    def _issuer_is_valid(self, issuer: str | None) -> bool:
        if not issuer:
            return False
        return issuer.startswith("https://login.microsoftonline.com/") and issuer.endswith("/v2.0")


class OAuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.providers = {
            OAuthProvider.GOOGLE: GoogleOAuthProvider(settings.GOOGLE_CLIENT_ID),
            OAuthProvider.MICROSOFT: MicrosoftOAuthProvider(settings.MICROSOFT_CLIENT_ID),
        }

    async def login(self, provider: OAuthProvider, token: str) -> dict:
        oauth_provider = self.providers.get(provider)
        if oauth_provider is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported OAuth provider",
            )
        return await oauth_provider.login(self.db, token)
