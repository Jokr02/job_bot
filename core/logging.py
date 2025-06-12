
import logging
import os
from logging.handlers import TimedRotatingFileHandler
import requests

ERROR_WEBHOOK_URL = os.getenv("ERROR_WEBHOOK_URL")

logger = logging.getLogger("jobbot")
logger.setLevel(logging.INFO)

def setup_logging():
    os.makedirs("logs", exist_ok=True)
    handler = TimedRotatingFileHandler("logs/jobbot.log", when="midnight", backupCount=7, encoding="utf-8")
    formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.addHandler(logging.StreamHandler())

def send_error_to_webhook(message: str):
    if ERROR_WEBHOOK_URL:
        try:
            requests.post(ERROR_WEBHOOK_URL, json={"content": f"❌ {message}"})
        except Exception:
            pass
