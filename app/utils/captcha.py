import logging

import httpx
from fastapi import HTTPException
from app.core.config import settings

logger = logging.getLogger(__name__)

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
                    # The client-facing detail stays generic; the reason lives in
                    # error-codes (e.g. timeout-or-duplicate = single-use token
                    # re-submitted, invalid-input-response = wrong/expired token
                    # or sitekey/secret pair mismatch). Log it for diagnosis.
                    logger.warning(
                        "Turnstile verification failed: error-codes=%s",
                        result.get("error-codes"),
                    )
                    raise HTTPException(status_code=400, detail="Cloudflare Turnstile verification failed")
        except httpx.RequestError:
            raise HTTPException(status_code=500, detail="Error communicating with captcha service")
