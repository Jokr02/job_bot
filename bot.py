import asyncio
import os
from dotenv import load_dotenv
from discord.ext import commands
import discord

from core.config_utils import load_config
from core.logging import logger, setup_logging, send_error_to_webhook
from core.cleanup import cleanup_old_messages, start_cleanup_loop
from core.jobs import search_jobs, start_job_loop
from commands.jobs import register_job_commands

load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

@bot.event
async def on_ready():
    logger.info(f"✅ Eingeloggt als {bot.user}")
    await tree.sync()
    await cleanup_old_messages(bot)
    start_job_loop(bot)
    start_cleanup_loop(bot)

register_job_commands(tree)

if __name__ == "__main__":
    setup_logging()
    bot.run(TOKEN)
