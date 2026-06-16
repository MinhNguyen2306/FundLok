from fastapi import APIRouter, BackgroundTasks
from app.contact.schemas import ContactRequest
from app.utils.email import send_contact_autoreply
from app.utils.captcha import verify_turnstile_token

router = APIRouter(prefix="/contact", tags=["contact"])

@router.post("")
def submit_contact_form(contact: ContactRequest, background_tasks: BackgroundTasks):
    verify_turnstile_token(contact.turnstile_token)

    # If verification succeeds, we send an auto-reply.
    background_tasks.add_task(send_contact_autoreply, to_email=contact.email, name=contact.name)

    return {"status": "success", "message": "Information received"}
