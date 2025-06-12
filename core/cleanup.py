import discord
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import os
import logging

logger = logging.getLogger("jobbot")

async def cleanup_old_messages(bot):
    try:
        channel_id = int(os.getenv("DISCORD_CHANNEL_ID"))
        channel = await bot.fetch_channel(channel_id)
        now = datetime.now(ZoneInfo("Europe/Berlin"))
        async for msg in channel.history(limit=200):
            if msg.author == bot.user and msg.created_at < now - timedelta(days=30):
                await msg.delete()
        logger.info("🧹 Alte Nachrichten gelöscht.")
    except Exception as e:
        logger.error(f"Fehler beim Aufräumen: {e}")
