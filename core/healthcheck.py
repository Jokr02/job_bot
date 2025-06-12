import socket
import platform
from datetime import datetime
import aiohttp
import os

async def get_system_info():
    return {
        "hostname": socket.gethostname(),
        "platform": platform.platform(),
        "timestamp": datetime.now().isoformat()
    }

async def send_healthcheck(bot_version="v1.0.0"):
    webhook_url = os.getenv("ERROR_WEBHOOK_URL")
    if not webhook_url:
        return

    info = await get_system_info()
    message = (
        f"✅ **JobBot gestartet**\n"
        f"**Version:** {bot_version}\n"
        f"**Host:** {info['hostname']}\n"
        f"**System:** {info['platform']}\n"
        f"**Zeitpunkt:** {info['timestamp']}"
    )
    try:
        async with aiohttp.ClientSession() as session:
            await session.post(webhook_url, json={"content": message}, timeout=10)
    except Exception as e:
        print(f"[HEALTHCHECK] Webhook fehlgeschlagen: {e}")

async def send_error_to_webhook(message: str):
    webhook_url = os.getenv("ERROR_WEBHOOK_URL")
    if not webhook_url:
        return
    try:
        async with aiohttp.ClientSession() as session:
            await session.post(webhook_url, json={"content": message}, timeout=10)
    except Exception as e:
        print(f"[ERROR] Webhook fehlgeschlagen: {e}")
