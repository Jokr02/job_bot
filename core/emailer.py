
import os
import smtplib
from email.message import EmailMessage
from core.logging import logger

def send_application_email(to_address, job_title, attachments=[]):
    try:
        smtp_server = os.getenv("SMTP_SERVER")
        smtp_port = int(os.getenv("SMTP_PORT", 587))
        smtp_user = os.getenv("SMTP_USER")
        smtp_password = os.getenv("SMTP_PASSWORD")
        sender_name = os.getenv("SENDER_NAME", "Max Mustermann")

        msg = EmailMessage()
        msg["Subject"] = f"Bewerbung: {job_title}"
        msg["From"] = f"{sender_name} <{smtp_user}>"
        msg["To"] = to_address
        msg.set_content(f"Sehr geehrte Damen und Herren,\n\nhiermit bewerbe ich mich auf die Stelle '{job_title}'.\nIm Anhang finden Sie meine Unterlagen.\n\nMit freundlichen Grüßen\n{sender_name}")

        for path in attachments:
            with open(path, "rb") as f:
                msg.add_attachment(f.read(), maintype="application", subtype="pdf", filename=os.path.basename(path))

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)

        logger.info(f"✅ Bewerbung an {to_address} gesendet.")
        return True
    except Exception as e:
        logger.error(f"Fehler beim Senden der E-Mail: {e}")
        return False
