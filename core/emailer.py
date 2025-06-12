import os
import smtplib
from email.message import EmailMessage
from core.logging import logger

def send_application_email(to_address, job_title, attachments=None):
    if attachments is None:
        attachments = [
            "data/anschreiben.pdf",
            "data/zeugnisse.pdf"
        ]

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
        msg.set_content(
            f"Sehr geehrte Damen und Herren,\n\n"
            f"hiermit bewerbe ich mich auf die Stelle '{job_title}'.\n"
            f"Im Anhang finden Sie meine Unterlagen.\n\n"
            f"Mit freundlichen Grüßen\n{sender_name}"
        )

        for path in attachments:
            try:
                with open(path, "rb") as f:
                    msg.add_attachment(
                        f.read(),
                        maintype="application",
                        subtype="pdf",
                        filename=os.path.basename(path)
                    )
            except FileNotFoundError:
                logger.warning(f"❌ Anhang nicht gefunden: {path}")

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)

        logger.info(f"📤 Bewerbung erfolgreich an {to_address} gesendet.")
        return True

    except Exception as e:
        logger.error(f"Fehler beim Senden der E-Mail: {e}")
        return False
