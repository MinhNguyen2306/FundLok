import smtplib
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING

from app.core.config import settings

# The brand mark, embedded in every HTML email rather than linked.
#
# WHY CID AND NOT A URL
# A hosted <img src="https://..."> is simpler, but it fails in the two places
# that matter: mail clients that block remote images show a broken box, and
# local development has no publicly reachable host at all, so every email sent
# through Mailpit would be logo-less. A CID part travels inside the message, so
# it renders offline, with images blocked, and in dev. A base64 data: URI is the
# third option and is not viable -- Gmail strips them.
_LOGO_PATH = Path(__file__).resolve().parents[1] / "assets" / "email-logo.png"

# Referenced from the HTML as <img src="cid:fundlok-logo">. The angle brackets
# belong in the header but never in the src.
_LOGO_CID = "fundlok-logo"


@lru_cache(maxsize=1)
def _logo_bytes() -> bytes | None:
    """The logo, read once per process. `None` if the asset is missing, which
    degrades to a text-only header rather than failing the send -- a password
    reset must not be blocked by a missing image."""
    try:
        return _LOGO_PATH.read_bytes()
    except OSError:
        return None


def brand_header() -> str:
    """The dark band that opens every email.

    Dark ground, not white: the brand mark is only ever placed on black or very
    dark teal (Handbook v3 §7.3), and the mark itself is the light-on-dark
    variant. `background-color` sits on the <td>, and the table is the layout --
    Outlook ignores CSS backgrounds on divs and does not do flexbox.

    Width is set in HTML attributes as well as CSS because Outlook reads the
    attribute and ignores the style.
    """
    if _logo_bytes() is None:
        return (
            '<tr><td align="center" style="background-color:#0a1512;'
            'padding:28px 20px;border-radius:12px 12px 0 0;">'
            '<span style="font-family:\'Helvetica Neue\',Arial,sans-serif;'
            'font-size:24px;font-weight:700;color:#ffffff;">Fund'
            '<span style="color:#84cc16;">Lok</span></span>'
            "</td></tr>"
        )
    return (
        '<tr><td align="center" style="background-color:#0a1512;'
        'padding:28px 20px;border-radius:12px 12px 0 0;">'
        f'<img src="cid:{_LOGO_CID}" alt="FundLok" width="180" height="64" '
        'style="display:block;width:180px;height:auto;border:0;outline:none;'
        'text-decoration:none;" />'
        "</td></tr>"
    )

if TYPE_CHECKING:
    # Type-only: app.contact.router imports this module, so a runtime import
    # back into app.contact would close the loop.
    from app.contact.schemas import ContactPurpose

def email_shell(body_html: str) -> str:
    """Wrap body content in the branded shell: dark logo band, white card, footer.

    Table-based and inline-styled on purpose. Email clients are not browsers --
    Outlook renders through Word, Gmail strips <style> blocks in some contexts,
    and neither does flexbox. Tables with inline styles are what actually works,
    which is why this does not look like the rest of the codebase's HTML.
    """
    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background-color:#f4f7f6;-webkit-font-smoothing:antialiased;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color:#f4f7f6;padding:24px 12px;">
    <tr><td align="center">
      <table role="presentation" width="600" cellpadding="0" cellspacing="0" border="0" style="max-width:600px;width:100%;">
        {brand_header()}
        <tr><td style="background-color:#ffffff;padding:36px 40px;font-family:'Helvetica Neue',Arial,sans-serif;color:#4b5563;font-size:16px;line-height:1.6;">
          {body_html}
        </td></tr>
        <tr><td style="background-color:#ffffff;border-radius:0 0 12px 12px;padding:0 40px 28px;font-family:'Helvetica Neue',Arial,sans-serif;">
          <p style="border-top:1px solid #e5e7eb;padding-top:18px;margin:0;color:#9ca3af;font-size:13px;text-align:center;">
            FundLok &middot; This is an automated message, please do not reply.
          </p>
        </td></tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""


def cta_button(href: str, label: str) -> str:
    """A centred call-to-action button.

    `color` is repeated inline on the anchor because some clients (notably
    Outlook and a few webmail readers) override link colour unless the anchor
    itself carries it -- white text on the green fill otherwise turns blue and
    becomes unreadable.
    """
    return f"""
      <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="margin:32px 0;">
        <tr><td align="center">
          <a href="{href}" style="display:inline-block;padding:14px 28px;background-color:#16a34a;color:#ffffff;text-decoration:none;border-radius:8px;font-weight:600;font-size:16px;font-family:'Helvetica Neue',Arial,sans-serif;">{label}</a>
        </td></tr>
      </table>"""


def send_email(
    to_email: str,
    subject: str,
    html_content: str,
    text_content: str | None = None,
    reply_to: str | None = None
) -> None:
    # 1. Create message
    #
    # multipart/related wrapping multipart/alternative -- the nesting matters.
    # The alternative part holds the text and HTML bodies so a client picks one;
    # the related part carries the HTML's inline images alongside it. Attaching
    # the image directly to an alternative part instead would advertise the logo
    # as a THIRD body the client may choose to render in place of the email.
    message = MIMEMultipart("related")
    message["Subject"] = subject
    message["From"] = f"{settings.EMAILS_FROM_NAME} <{settings.EMAILS_FROM_EMAIL}>"
    message["To"] = to_email
    if reply_to:
        message["Reply-To"] = reply_to

    if not text_content:
        text_content = "Please view this email in an HTML-compatible client."

    body = MIMEMultipart("alternative")
    body.attach(MIMEText(text_content, "plain"))
    body.attach(MIMEText(html_content, "html"))
    message.attach(body)

    logo = _logo_bytes()
    if logo is not None:
        image = MIMEImage(logo, "png")
        # Angle brackets are part of the Content-ID header syntax; the HTML
        # refers to the bare id. Getting this wrong is the usual reason a CID
        # image renders as a broken box.
        image.add_header("Content-ID", f"<{_LOGO_CID}>")
        # "inline" keeps it out of the client's attachment list -- without it
        # every email arrives looking like it has a file attached.
        image.add_header("Content-Disposition", "inline", filename="fundlok.png")
        message.attach(image)

    # 2. Connect and send
    if settings.SMTP_SECURE:
        server = smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT)
    else:
        server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)
        
    try:
        if settings.SMTP_USER and settings.SMTP_PASSWORD:
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.sendmail(settings.EMAILS_FROM_EMAIL, to_email, message.as_string())
    finally:
        server.quit()


def send_verification_email(to_email: str, token: str) -> None:
    from datetime import datetime
    # We construct a verification link. Let's make it point to the backend route or frontend route.
    # The requirement is: "it attach a button for user to click on it will local to somewhere to verify user email"
    # We will point it to the frontend verify URL: {FRONTEND_URL}/verify-email?token={token}
    verification_link = f"{settings.FRONTEND_URL}/verify-email?token={token}"
    
    subject = "Verify your email for FundLok"
    
    html_content = email_shell(
        f"""
          <h1 style="margin:0 0 20px;font-size:24px;font-weight:700;color:#111827;">Verify Your Email Address</h1>
          <p>Thank you for signing up with <strong>FundLok</strong>. To activate your account and start investing or raising funds, please verify your email address by clicking the button below:</p>
          {cta_button(verification_link, "Verify Email")}
          <p>If the button doesn't work, you can copy and paste the following link into your browser:</p>
          <p style="word-break:break-all;"><a href="{verification_link}" style="color:#16a34a;">{verification_link}</a></p>
          <p>This verification link will expire in 24 hours.</p>
          <p style="color:#9ca3af;font-size:13px;">&copy; {datetime.now().year} FundLok. All rights reserved.</p>
        """
    )

    text_content = f"Please verify your email by visiting this link: {verification_link}"
    
    send_email(
        to_email=to_email,
        subject=subject,
        html_content=html_content,
        text_content=text_content
    )

def send_contact_autoreply(to_email: str, name: str) -> None:
    subject = "We have received your message - FundLok"
    
    html_content = email_shell(
        f"""
          <h2 style="margin:0 0 20px;font-size:22px;color:#111827;">Thank you for contacting FundLok!</h2>
          <p>Hi {name},</p>
          <p>We have successfully received your information. Our team will review your message and get back to you as soon as possible.</p>
          <p>Best regards,<br/>The FundLok Team</p>
        """
    )
    
    text_content = f"Hi {name},\n\nWe have successfully received your information. Our team will review your message and get back to you as soon as possible.\n\nBest regards,\nThe FundLok Team"

    send_email(
        to_email=to_email,
        subject=subject,
        html_content=html_content,
        text_content=text_content
    )


def send_contact_notification(
    name: str,
    email: str,
    message: str,
    subject: str | None = None,
    purpose: "ContactPurpose | None" = None
) -> None:
    """Forward a contact-form submission to the team inbox.

    Everything here comes from an anonymous public form, so every field is
    HTML-escaped before it reaches the template. The submitter's address is set
    as Reply-To rather than From: sending as them would fail SPF/DKIM for our
    domain and land the notification in spam.

    The subject is prefixed with the purpose the sender picked
    ("[Partnership] …"), so the inbox can be filtered and triaged on the header
    alone. The prefix comes from the server-side enum label, never from the
    request body.
    """
    import html as html_lib

    # Subject and name land in a mail header, so newlines are stripped out
    # (they would otherwise let a submitter inject extra headers) and the
    # result is capped to keep the header a sane length.
    def header_safe(value: str) -> str:
        return " ".join(value.split())[:120]

    topic = header_safe(subject or "") or "(no subject)"
    name = header_safe(name) or "(no name)"
    # "General" covers a submission from a cached bundle that predates the
    # dropdown, so the subject shape stays constant for inbox filters.
    purpose_label = purpose.label if purpose else "General"

    safe_name = html_lib.escape(name)
    safe_email = html_lib.escape(email)
    safe_topic = html_lib.escape(topic)
    safe_purpose = html_lib.escape(purpose_label)
    safe_message = html_lib.escape(message).replace("\n", "<br/>")

    label = (
        "color:#9ca3af;font-size:12px;text-transform:uppercase;"
        "letter-spacing:0.08em;"
    )
    html_content = email_shell(
        f"""
          <h1 style="margin:0 0 24px;font-size:20px;font-weight:700;color:#111827;">New contact form submission</h1>
          <p style="margin:0 0 8px;"><span style="{label}">Purpose</span><br/>{safe_purpose}</p>
          <p style="margin:0 0 8px;"><span style="{label}">Name</span><br/>{safe_name}</p>
          <p style="margin:0 0 8px;"><span style="{label}">Email</span><br/><a href="mailto:{safe_email}" style="color:#16a34a;">{safe_email}</a></p>
          <p style="margin:0 0 8px;"><span style="{label}">Subject</span><br/>{safe_topic}</p>
          <p style="margin:0 0 8px;"><span style="{label}">Message</span></p>
          <div style="color:#111827;font-size:15px;line-height:1.6;background-color:#f9fafb;border-radius:8px;padding:16px;margin-top:8px;white-space:pre-wrap;">{safe_message}</div>
        """
    )

    text_content = (
        f"New contact form submission\n\n"
        f"Purpose: {purpose_label}\n"
        f"Name: {name}\n"
        f"Email: {email}\n"
        f"Subject: {topic}\n\n"
        f"Message:\n{message}\n"
    )

    send_email(
        to_email=settings.CONTACT_INBOX_EMAIL,
        subject=f"[{purpose_label}] {topic} - {name}",
        html_content=html_content,
        text_content=text_content,
        reply_to=email
    )


def send_password_reset_email(to_email: str, token: str) -> None:
    from datetime import datetime
    reset_link = f"{settings.FRONTEND_URL}/reset-password?token={token}"
    
    subject = "Reset your password for FundLok"
    
    html_content = email_shell(
        f"""
          <h1 style="margin:0 0 20px;font-size:24px;font-weight:700;color:#111827;">Reset Your Password</h1>
          <p>You requested to reset your password for your <strong>FundLok</strong> account. Click the button below to set a new password:</p>
          {cta_button(reset_link, "Reset Password")}
          <p>If the button doesn't work, you can copy and paste the following link into your browser:</p>
          <p style="word-break:break-all;"><a href="{reset_link}" style="color:#16a34a;">{reset_link}</a></p>
          <p>This password reset link will expire in 1 hour.</p>
          <p>If you did not request a password reset, please ignore this email.</p>
          <p style="color:#9ca3af;font-size:13px;">&copy; {datetime.now().year} FundLok. All rights reserved.</p>
        """
    )

    text_content = f"Please reset your password by visiting this link: {reset_link}"

    send_email(
        to_email=to_email,
        subject=subject,
        html_content=html_content,
        text_content=text_content
    )


def send_password_changed_notice(to_email: str, first_time: bool = False) -> None:
    """Tell the account owner their password just changed.

    Purely a security notification -- it carries no token and grants nothing.
    Its whole job is to make an unauthorised change visible to the real owner
    while they can still act on it, which is why it always names the recovery
    route. Send it AFTER the change has been committed, so the email never
    describes something that didn't happen.

    `first_time` swaps the wording for an account setting its first password
    (the OAuth case) -- "was changed" would be untrue there.
    """
    from datetime import datetime

    reset_link = f"{settings.FRONTEND_URL}/forgot-password"

    subject = (
        "Your FundLok password was set"
        if first_time
        else "Your FundLok password was changed"
    )
    headline = "Your password was set" if first_time else "Your password was changed"
    lede = (
        "A password was just added to your <strong>FundLok</strong> account. You can now "
        "sign in with your email address and password."
        if first_time
        else "The password on your <strong>FundLok</strong> account was just changed."
    )

    html_content = email_shell(
        f"""
          <h1 style="margin:0 0 20px;font-size:24px;font-weight:700;color:#111827;">{headline}</h1>
          <p>{lede}</p>
          <p>If this was you, nothing further is needed — you can ignore this email.</p>
          <p><strong>If this wasn't you</strong>, reset your password immediately using the button
          below, and contact us so we can secure your account.</p>
          {cta_button(reset_link, "Reset your password")}
          <p style="color:#9ca3af;font-size:13px;">&copy; {datetime.now().year} FundLok. All rights reserved.</p>
        """
    )

    text_content = (
        (
            "A password was just added to your FundLok account. You can now sign in "
            "with your email address and password."
            if first_time
            else "The password on your FundLok account was just changed."
        )
        + " If this was you, no action is needed. If it wasn't, reset your password "
        f"immediately at {reset_link} and contact us so we can secure your account."
    )

    send_email(
        to_email=to_email,
        subject=subject,
        html_content=html_content,
        text_content=text_content,
    )


def send_existing_account_notice(to_email: str) -> None:
    """Notify the real owner that someone tried to register with their email.

    Sent instead of a verification email when registration hits an
    already-registered address. This lets the legitimate owner react (log in
    or reset their password) without the registration endpoint ever confirming
    to the submitter that the account exists — the anti-enumeration guarantee.
    """
    from datetime import datetime

    login_link = f"{settings.FRONTEND_URL}/login"
    reset_link = f"{settings.FRONTEND_URL}/forgot-password"

    subject = "About your FundLok account"

    html_content = email_shell(
        f"""
          <h1 style="margin:0 0 20px;font-size:24px;font-weight:700;color:#111827;">Your account already exists</h1>
          <p>We received a request to create a new <strong>FundLok</strong> account with this email address, but you already have one.</p>
          <p>If this was you, just sign in — there's no need to register again. If you've forgotten your password, you can reset it.</p>
          {cta_button(login_link, "Sign in")}
          <p>Forgot your password? <a href="{reset_link}" style="color:#16a34a;">Reset it here</a>.</p>
          <p>If you did not try to register, you can safely ignore this email — no changes were made to your account.</p>
          <p style="color:#9ca3af;font-size:13px;">&copy; {datetime.now().year} FundLok. All rights reserved.</p>
        """
    )

    text_content = (
        "We received a request to create a FundLok account with this email, but "
        f"you already have one. Sign in at {login_link} or reset your password at "
        f"{reset_link}. If this wasn't you, you can ignore this email."
    )

    send_email(
        to_email=to_email,
        subject=subject,
        html_content=html_content,
        text_content=text_content,
    )


def send_new_device_signin_alert(
    to_email: str, *, device: str, browser: str, ip_address: str | None
) -> None:
    """Tell the owner a device we have not seen before just signed in.

    Same contract as send_password_changed_notice: a notification, no token, no
    action it can be tricked into performing. Its job is to make an
    unauthorised sign-in visible while the owner can still act, so it names the
    two things they would do next -- change the password, or sign the device out
    from the security screen.

    Sent only when the account has sign-in alerts switched on
    (users.signin_alerts_enabled), and only for an unrecognised device: mailing
    on every sign-in trains people to ignore it.
    """
    security_link = f"{settings.FRONTEND_URL}/dashboard/security"
    reset_link = f"{settings.FRONTEND_URL}/forgot-password"
    where = ip_address or "an unknown address"

    html_content = email_shell(
        f"""
          <h1 style="margin:0 0 16px;font-size:22px;font-weight:700;color:#111827;">New sign-in to your FundLok account</h1>
          <p>Someone signed in from <strong>{browser} on {device}</strong> ({where}).
          If that was you, nothing more is needed.</p>
          <p>If it was not you, sign that device out and change your password now:</p>
          {cta_button(security_link, "Review signed-in devices")}
          <p style="color:#6b7280;font-size:13px;">
            You can also <a href="{reset_link}" style="color:#16a34a;">reset your password</a>. This email was sent
            because sign-in alerts are switched on for your account.
          </p>
        """
    )

    send_email(
        to_email=to_email,
        subject="New sign-in to your FundLok account",
        html_content=html_content,
    )
