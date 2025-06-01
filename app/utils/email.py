# app/utils/email.py

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import config

async def send_email(to_email: str, subject: str, body: str):
    message = MIMEMultipart("alternative")
    message["From"] = config.SMTP_FROM_EMAIL
    message["To"] = to_email
    message["Subject"] = subject

    # Plain text fallback
    text = body

    # HTML version of the email
    html = f"""
    <html>
      <body>
        <p>{body}</p>
      </body>
    </html>
    """

    message.attach(MIMEText(text, "plain"))
    message.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP(config.SMTP_SERVER, config.SMTP_PORT) as server:
            server.starttls()
            server.login(config.SMTP_USERNAME, config.SMTP_PASSWORD)
            server.sendmail(
                from_addr=config.SMTP_FROM_EMAIL,
                to_addrs=[to_email],
                msg=message.as_string()
            )
    except Exception as e:
        print(f"[EMAIL ERROR] Failed to send email to {to_email}: {e}")
