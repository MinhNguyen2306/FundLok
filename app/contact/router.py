from fastapi import APIRouter, BackgroundTasks
from app.contact.schemas import ContactRequest
from app.utils.email import send_contact_autoreply, send_contact_notification
from app.utils.captcha import verify_turnstile_token

router = APIRouter(prefix="/contact", tags=["contact"])

@router.post("")
def submit_contact_form(contact: ContactRequest, background_tasks: BackgroundTasks):
    verify_turnstile_token(contact.turnstile_token)

    # Forward the submission to the team inbox (CONTACT_INBOX_EMAIL) — without
    # this the message body only ever existed in the request.
    background_tasks.add_task(
        send_contact_notification,
        name=contact.name,
        email=contact.email,
        subject=contact.subject,
        message=contact.message,
        purpose=contact.purpose,
    )

    # ...and acknowledge to the sender.
    background_tasks.add_task(send_contact_autoreply, to_email=contact.email, name=contact.name)

    return {"status": "success", "message": "Information received"}
