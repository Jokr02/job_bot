
from datetime import datetime, timedelta
import discord
from core.logging import logger, send_error_to_webhook
import os

CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))

async def cleanup_old_messages(bot):
    try:
        channel = await bot.fetch_channel(CHANNEL_ID)
        cutoff = datetime.utcnow() - timedelta(days=30)
        deleted = 0
        async for message in channel.history(limit=100):
            if message.author == bot.user and message.created_at < cutoff:
                await message.delete()
                deleted += 1
        if deleted:
            logger.info(f"🧹 {deleted} alte Nachrichten gelöscht.")
            send_error_to_webhook(f"🧹 {deleted} alte Nachrichten im Channel gelöscht.")
    except Exception as e:
        logger.error(f"Fehler beim Aufräumen: {e}")
        send_error_to_webhook(f"Fehler beim Aufräumen: {e}")

def start_cleanup_loop(bot):
    async def loop():
        await bot.wait_until_ready()
        while not bot.is_closed():
            await cleanup_old_messages(bot)
            await asyncio.sleep(86400)
    import asyncio
    bot.loop.create_task(loop())
