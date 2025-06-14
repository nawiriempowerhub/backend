import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from fastapi import HTTPException

async def send_notification(subject: str, body: str):
    """
    Send a notification email to Nawiri's Gmail account.
    Args:
        subject: Email subject
        body: Plain text body
    """
    msg = MIMEMultipart()
    msg['From'] = os.getenv("SMTP_USER")
    msg['To'] = os.getenv("TO_EMAIL")
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))
    print("SMTP_USER:", os.getenv("SMTP_USER"))
    print("SMTP_PASS:", os.getenv("SMTP_PASS"))

    try:
        server = smtplib.SMTP(os.getenv("SMTP_HOST"), int(os.getenv("SMTP_PORT")))
        server.starttls()
        server.login(os.getenv("SMTP_USER"), os.getenv("SMTP_PASS"))
        server.sendmail(msg['From'], msg['To'], msg.as_string())
        server.quit()
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Email sending failed: {str(e)}")