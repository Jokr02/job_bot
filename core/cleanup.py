import os
import json
import asyncio
from datetime import datetime, timedelta
import discord
from zoneinfo import ZoneInfo

from core.config_utils import load_config
from core.logging import logger, send_error_to_webhook
from core.jobs import load_seen_jobs

DISCORD_TIMEZONE = ZoneInfo("Europe/Berlin")
MAX_MESSAGE_AGE_DAYS = 30

async def cleanup_old_messages(bot: discord.Client):
    try:
        config = load_config()
        channel_id = int(os.getenv("DISCORD_CHANNEL_ID", "0"))
        if channel_id == 0:
            logger.warning("⚠️ DISCORD_CHANNEL_ID ist nicht gesetzt.")
            return

        channel = await bot.fetch_channel(channel_id)
        now = datetime.now(DISCORD_TIMEZONE)
        cutoff = now - timedelta(days=MAX_MESSAGE_AGE_DAYS)

        async for message in channel.history(limit=500):
            if message.created_at.replace(tzinfo=ZoneInfo("UTC")) < cutoff:
                try:
                    await message.delete()
                    await asyncio.sleep(1)  # Rate limit beachten
                except Exception as e:
                    logger.warning(f"⚠️ Fehler beim Löschen von Nachricht {message.id}: {e}")
        logger.info("🧹 Alte Nachrichten bereinigt.")
    except Exception as e:
        logger.error(f"Fehler beim Aufräumen: {e}")
        await send_error_to_webhook(f"❌ Fehler beim Aufräumen: {e}")

def start_cleanup_loop(bot: discord.Client):
    async def loop():
        while True:
            await asyncio.sleep(3600)  # 1x pro Stunde
            await cleanup_old_messages(bot)
    asyncio.create_task(loop())
