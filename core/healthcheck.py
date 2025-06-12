import socket
import platform
from datetime import datetime
import requests

def get_system_info():
    return {
        "hostname": socket.gethostname(),
        "platform": platform.platform(),
        "timestamp": datetime.now().isoformat()
    }

def send_healthcheck(webhook_url, bot_version="v1.0.0"):
    info = get_system_info()
    message = (
        f"✅ **JobBot gestartet**\n"
        f"**Version:** {bot_version}\n"
        f"**Host:** {info['hostname']}\n"
        f"**System:** {info['platform']}\n"
        f"**Zeitpunkt:** {info['timestamp']}"
    )
    try:
        requests.post(webhook_url, json={"content": message}, timeout=10)
    except Exception as e:
        print(f"[HEALTHCHECK] Webhook fehlgeschlagen: {e}")
