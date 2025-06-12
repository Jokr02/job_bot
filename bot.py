import asyncio
import os
from dotenv import load_dotenv
from discord.ext import commands
import discord

from core.config_utils import load_config
from core.logging import logger, setup_logging, send_error_to_webhook
from core.cleanup import cleanup_old_messages, start_cleanup_loop
from core.jobs import search_jobs, start_job_loop
from core.healthcheck import send_healthcheck
from commands.jobs import register_job_commands

# ------------------- ENV + Token -------------------
load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))

# ------------------- Discord Bot Setup -------------------
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# ------------------- Bot Ready Event -------------------
@bot.event
async def on_ready():
    logger.info(f"✅ Eingeloggt als {bot.user}")
    await tree.sync()

    try:
        await send_healthcheck(bot)  # Health-Info an Webhook
        await cleanup_old_messages(bot)  # Alte Nachrichten löschen
        start_job_loop(bot)             # Jobsuche starten
        start_cleanup_loop(bot)         # Nachrichten-Cleanup starten
    except Exception as e:
        logger.error(f"Fehler im on_ready: {e}")
        await send_error_to_webhook(f"❌ Fehler beim Start: {e}")

# ------------------- Slash-Commands Registrieren -------------------
register_job_commands(tree)

# ------------------- Starten -------------------
if __name__ == "__main__":
    setup_logging()
    bot.run(TOKEN)
