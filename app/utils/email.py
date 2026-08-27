import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from app.core.config import settings

def send_email(
    to_email: str,
    subject: str,
    html_content: str,
    text_content: str | None = None
) -> None:
    # 1. Create message
    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = f"{settings.EMAILS_FROM_NAME} <{settings.EMAILS_FROM_EMAIL}>"
    message["To"] = to_email

    if not text_content:
        text_content = "Please view this email in an HTML-compatible client."

    message.attach(MIMEText(text_content, "plain"))
    message.attach(MIMEText(html_content, "html"))

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
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <style>
        body {{ font-family: 'Helvetica Neue', Arial, sans-serif; background-color: #f4f7f6; margin: 0; padding: 0; -webkit-font-smoothing: antialiased; }}
        .wrapper {{ background-color: #f4f7f6; padding: 20px; }}
        .container {{ max-width: 600px; margin: 40px auto; background-color: #ffffff; padding: 40px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05); }}
        .header {{ text-align: center; margin-bottom: 30px; }}
        .title {{ color: #111827; font-size: 24px; font-weight: 700; margin: 0; }}
        .content {{ color: #4b5563; font-size: 16px; line-height: 1.6; margin-bottom: 30px; }}
        .cta-container {{ text-align: center; margin: 35px 0; }}
        .cta-button {{ display: inline-block; padding: 14px 28px; background-color: #16a34a; color: #ffffff !important; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px; box-shadow: 0 4px 6px -1px rgba(22, 163, 74, 0.25); }}
        .footer {{ text-align: center; color: #9ca3af; font-size: 13px; border-top: 1px solid #e5e7eb; padding-top: 20px; margin-top: 20px; }}
      </style>
    </head>
    <body>
      <div class="wrapper">
        <div class="container">
          <div class="header">
            <h1 class="title">Verify Your Email Address</h1>
          </div>
          <div class="content">
            <p>Thank you for signing up with <strong>FundLok</strong>. To activate your account and start investing or raising funds, please verify your email address by clicking the button below:</p>
          </div>
          <div class="cta-container">
            <a href="{verification_link}" class="cta-button" style="color: #ffffff;">Verify Email</a>
          </div>
          <div class="content">
            <p>If the button doesn't work, you can copy and paste the following link into your browser:</p>
            <p style="word-break: break-all;"><a href="{verification_link}" style="color: #16a34a;">{verification_link}</a></p>
            <p>This verification link will expire in 24 hours.</p>
          </div>
          <div class="footer">
            <p>&copy; {datetime.now().year} FundLok. All rights reserved.</p>
          </div>
        </div>
      </div>
    </body>
    </html>
    """
    
    text_content = f"Please verify your email by visiting this link: {verification_link}"
    
    send_email(
        to_email=to_email,
        subject=subject,
        html_content=html_content,
        text_content=text_content
    )

def send_contact_autoreply(to_email: str, name: str) -> None:
    subject = "We have received your message - FundLok"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <style>
        body {{ font-family: 'Helvetica Neue', Arial, sans-serif; background-color: #f4f7f6; margin: 0; padding: 0; }}
        .wrapper {{ background-color: #f4f7f6; padding: 20px; }}
        .container {{ max-width: 600px; margin: 40px auto; background-color: #ffffff; padding: 40px; border-radius: 12px; }}
        .header {{ text-align: center; margin-bottom: 30px; }}
        .content {{ color: #4b5563; font-size: 16px; line-height: 1.6; margin-bottom: 30px; }}
      </style>
    </head>
    <body>
      <div class="wrapper">
        <div class="container">
          <div class="header">
            <h2>Thank you for contacting FundLok!</h2>
          </div>
          <div class="content">
            <p>Hi {name},</p>
            <p>We have successfully received your information. Our team will review your message and get back to you as soon as possible.</p>
            <p>Best regards,<br/>The FundLok Team</p>
          </div>
        </div>
      </div>
    </body>
    </html>
    """
    
    text_content = f"Hi {name},\n\nWe have successfully received your information. Our team will review your message and get back to you as soon as possible.\n\nBest regards,\nThe FundLok Team"
    
    send_email(
        to_email=to_email,
        subject=subject,
        html_content=html_content,
        text_content=text_content
    )


def send_password_reset_email(to_email: str, token: str) -> None:
    from datetime import datetime
    reset_link = f"{settings.FRONTEND_URL}/reset-password?token={token}"
    
    subject = "Reset your password for FundLok"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <style>
        body {{ font-family: 'Helvetica Neue', Arial, sans-serif; background-color: #f4f7f6; margin: 0; padding: 0; -webkit-font-smoothing: antialiased; }}
        .wrapper {{ background-color: #f4f7f6; padding: 20px; }}
        .container {{ max-width: 600px; margin: 40px auto; background-color: #ffffff; padding: 40px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05); }}
        .header {{ text-align: center; margin-bottom: 30px; }}
        .title {{ color: #111827; font-size: 24px; font-weight: 700; margin: 0; }}
        .content {{ color: #4b5563; font-size: 16px; line-height: 1.6; margin-bottom: 30px; }}
        .cta-container {{ text-align: center; margin: 35px 0; }}
        .cta-button {{ display: inline-block; padding: 14px 28px; background-color: #16a34a; color: #ffffff !important; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px; box-shadow: 0 4px 6px -1px rgba(22, 163, 74, 0.25); }}
        .footer {{ text-align: center; color: #9ca3af; font-size: 13px; border-top: 1px solid #e5e7eb; padding-top: 20px; margin-top: 20px; }}
      </style>
    </head>
    <body>
      <div class="wrapper">
        <div class="container">
          <div class="header">
            <h1 class="title">Reset Your Password</h1>
          </div>
          <div class="content">
            <p>You requested to reset your password for your <strong>FundLok</strong> account. Click the button below to set a new password:</p>
          </div>
          <div class="cta-container">
            <a href="{reset_link}" class="cta-button" style="color: #ffffff;">Reset Password</a>
          </div>
          <div class="content">
            <p>If the button doesn't work, you can copy and paste the following link into your browser:</p>
            <p style="word-break: break-all;"><a href="{reset_link}" style="color: #16a34a;">{reset_link}</a></p>
            <p>This password reset link will expire in 1 hour.</p>
            <p>If you did not request a password reset, please ignore this email.</p>
          </div>
          <div class="footer">
            <p>&copy; {datetime.now().year} FundLok. All rights reserved.</p>
          </div>
        </div>
      </div>
    </body>
    </html>
    """
    
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

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <style>
        body {{ font-family: 'Helvetica Neue', Arial, sans-serif; background-color: #f4f7f6; margin: 0; padding: 0; -webkit-font-smoothing: antialiased; }}
        .wrapper {{ background-color: #f4f7f6; padding: 20px; }}
        .container {{ max-width: 600px; margin: 40px auto; background-color: #ffffff; padding: 40px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05); }}
        .header {{ text-align: center; margin-bottom: 30px; }}
        .title {{ color: #111827; font-size: 24px; font-weight: 700; margin: 0; }}
        .content {{ color: #4b5563; font-size: 16px; line-height: 1.6; margin-bottom: 30px; }}
        .cta-container {{ text-align: center; margin: 35px 0; }}
        .cta-button {{ display: inline-block; padding: 14px 28px; background-color: #16a34a; color: #ffffff !important; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px; box-shadow: 0 4px 6px -1px rgba(22, 163, 74, 0.25); }}
        .footer {{ text-align: center; color: #9ca3af; font-size: 13px; border-top: 1px solid #e5e7eb; padding-top: 20px; margin-top: 20px; }}
      </style>
    </head>
    <body>
      <div class="wrapper">
        <div class="container">
          <div class="header">
            <h1 class="title">{headline}</h1>
          </div>
          <div class="content">
            <p>{lede}</p>
            <p>If this was you, nothing further is needed — you can ignore this email.</p>
            <p><strong>If this wasn't you</strong>, reset your password immediately using the button
            below, and contact us so we can secure your account.</p>
          </div>
          <div class="cta-container">
            <a href="{reset_link}" class="cta-button" style="color: #ffffff;">Reset your password</a>
          </div>
          <div class="footer">
            <p>&copy; {datetime.now().year} FundLok. All rights reserved.</p>
          </div>
        </div>
      </div>
    </html>
    """

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

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <style>
        body {{ font-family: 'Helvetica Neue', Arial, sans-serif; background-color: #f4f7f6; margin: 0; padding: 0; -webkit-font-smoothing: antialiased; }}
        .wrapper {{ background-color: #f4f7f6; padding: 20px; }}
        .container {{ max-width: 600px; margin: 40px auto; background-color: #ffffff; padding: 40px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05); }}
        .header {{ text-align: center; margin-bottom: 30px; }}
        .title {{ color: #111827; font-size: 24px; font-weight: 700; margin: 0; }}
        .content {{ color: #4b5563; font-size: 16px; line-height: 1.6; margin-bottom: 30px; }}
        .cta-container {{ text-align: center; margin: 35px 0; }}
        .cta-button {{ display: inline-block; padding: 14px 28px; background-color: #16a34a; color: #ffffff !important; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px; box-shadow: 0 4px 6px -1px rgba(22, 163, 74, 0.25); }}
        .footer {{ text-align: center; color: #9ca3af; font-size: 13px; border-top: 1px solid #e5e7eb; padding-top: 20px; margin-top: 20px; }}
      </style>
    </head>
    <body>
      <div class="wrapper">
        <div class="container">
          <div class="header">
            <h1 class="title">Your account already exists</h1>
          </div>
          <div class="content">
            <p>We received a request to create a new <strong>FundLok</strong> account with this email address, but you already have one.</p>
            <p>If this was you, just sign in — there's no need to register again. If you've forgotten your password, you can reset it.</p>
          </div>
          <div class="cta-container">
            <a href="{login_link}" class="cta-button" style="color: #ffffff;">Sign in</a>
          </div>
          <div class="content">
            <p>Forgot your password? <a href="{reset_link}" style="color: #16a34a;">Reset it here</a>.</p>
            <p>If you did not try to register, you can safely ignore this email — no changes were made to your account.</p>
          </div>
          <div class="footer">
            <p>&copy; {datetime.now().year} FundLok. All rights reserved.</p>
          </div>
        </div>
      </div>
    </body>
    </html>
    """

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

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style="font-family: 'Helvetica Neue', Arial, sans-serif; background:#f4f7f6; margin:0; padding:20px;">
      <div style="max-width:600px;margin:40px auto;background:#fff;padding:40px;border-radius:12px;">
        <h1 style="font-size:22px;color:#111;margin:0 0 16px;">New sign-in to your FundLok account</h1>
        <p style="color:#444;line-height:1.6;">
          Someone signed in from <strong>{browser} on {device}</strong> ({where}).
          If that was you, nothing more is needed.
        </p>
        <p style="color:#444;line-height:1.6;">
          If it was not you, sign that device out and change your password now:
        </p>
        <p style="margin:24px 0;">
          <a href="{security_link}" style="background:#0f766e;color:#fff;padding:12px 20px;border-radius:8px;text-decoration:none;">Review signed-in devices</a>
        </p>
        <p style="color:#666;font-size:13px;line-height:1.6;">
          You can also <a href="{reset_link}">reset your password</a>. This email was sent
          because sign-in alerts are switched on for your account.
        </p>
      </div>
    </body>
    </html>
    """

    send_email(
        to_email=to_email,
        subject="New sign-in to your FundLok account",
        html_content=html_content,
    )
