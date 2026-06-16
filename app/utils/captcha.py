import httpx
from fastapi import HTTPException
from app.core.config import settings

def verify_turnstile_token(token: str | None) -> None:
    """
    Verifies the Cloudflare Turnstile token.
    Raises HTTPException if verification fails or the token is missing when required.
    """
    if settings.CLOUDFLARE_TURNSTILE_SECRET_KEY:
        if not token:
            raise HTTPException(status_code=400, detail="Turnstile token is missing")

        verify_url = "https://challenges.cloudflare.com/turnstile/v0/siteverify"
        payload = {
            "secret": settings.CLOUDFLARE_TURNSTILE_SECRET_KEY,
            "response": token
        }
        try:
            with httpx.Client() as client:
                resp = client.post(verify_url, data=payload)
                result = resp.json()
                if not result.get("success"):
                    raise HTTPException(status_code=400, detail="Cloudflare Turnstile verification failed")
        except httpx.RequestError:
            raise HTTPException(status_code=500, detail="Error communicating with captcha service")
