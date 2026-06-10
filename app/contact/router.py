from fastapi import APIRouter, HTTPException, BackgroundTasks
import httpx
from app.core.config import settings
from app.contact.schemas import ContactRequest
from app.utils.email import send_contact_autoreply

router = APIRouter(prefix="/contact", tags=["contact"])

@router.post("")
def submit_contact_form(contact: ContactRequest, background_tasks: BackgroundTasks):
    if settings.CLOUDFLARE_TURNSTILE_SECRET_KEY:
        if not contact.turnstile_token:
            raise HTTPException(status_code=400, detail="Turnstile token is missing")

        verify_url = "https://challenges.cloudflare.com/turnstile/v0/siteverify"
        payload = {
            "secret": settings.CLOUDFLARE_TURNSTILE_SECRET_KEY,
            "response": contact.turnstile_token
        }
        try:
            with httpx.Client() as client:
                resp = client.post(verify_url, data=payload)
                result = resp.json()
                if not result.get("success"):
                    raise HTTPException(status_code=400, detail="Cloudflare Turnstile verification failed")
        except httpx.RequestError:
            raise HTTPException(status_code=500, detail="Error communicating with captcha service")

    # If verification succeeds, we send an auto-reply.
    background_tasks.add_task(send_contact_autoreply, to_email=contact.email, name=contact.name)

    return {"status": "success", "message": "Information received"}
