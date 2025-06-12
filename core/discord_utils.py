import discord
import logging
from discord import ButtonStyle
from discord.ui import View, Button
from core.storage import save_job

logger = logging.getLogger(__name__)

class JobView(View):
    def __init__(self, job):
        super().__init__(timeout=None)
        self.job = job

    @discord.ui.button(label="💾 Save", style=ButtonStyle.green)
    async def save_button(self, interaction: discord.Interaction, button: Button):
        save_job(self.job)
        await interaction.response.send_message("✅ Job gespeichert!", ephemeral=True)

    @discord.ui.button(label="⏭️ Skip", style=ButtonStyle.grey)
    async def skip_button(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message("⏩ Übersprungen.", ephemeral=True)

async def send_job_to_discord(job):
    from bot import bot, CHANNEL_ID
    try:
        channel = await bot.fetch_channel(CHANNEL_ID)
        desc = f"💼 **{job['title']}**\n🏢 {job['company']}\n📍 {job['location']}\n🔗 {job['url']}"
        await channel.send(desc, view=JobView(job))
    except Exception as e:
        logger.error(f"Fehler beim Senden an Discord: {e}")
