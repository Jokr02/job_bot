import discord
import asyncio
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from core.config_utils import load_config
from core.jobs import load_seen_jobs
from core.logging import logger, send_error_to_webhook

async def cleanup_old_messages(bot: discord.Client):
    try:
        config = load_config()
        channel = await bot.fetch_channel(int(config["channel_id"]))
        seen_ids = load_seen_jobs()
        cutoff = datetime.now(ZoneInfo("Europe/Berlin")) - timedelta(days=30)

        async for message in channel.history(limit=200):
            if message.author == bot.user and message.created_at.replace(tzinfo=ZoneInfo("UTC")) < cutoff:
                if any(job_id in message.content for job_id in seen_ids):
                    await message.delete()
        logger.info("🧹 Alte Nachrichten bereinigt.")
    except Exception as e:
        logger.error(f"Fehler beim Aufräumen: {e}")
        await send_error_to_webhook(f"Fehler beim Aufräumen: {e}")

def start_cleanup_loop(bot: discord.Client):
    async def loop():
        while True:
            await cleanup_old_messages(bot)
            await asyncio.sleep(3600 * 6)  # alle 6 Stunden
    asyncio.create_task(loop())
