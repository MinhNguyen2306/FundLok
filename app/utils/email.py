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
        .cta-button {{ display: inline-block; padding: 14px 28px; background-color: #4f46e5; color: #ffffff !important; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px; box-shadow: 0 4px 6px -1px rgba(79, 70, 229, 0.2); }}
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
            <p style="word-break: break-all;"><a href="{verification_link}" style="color: #4f46e5;">{verification_link}</a></p>
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
