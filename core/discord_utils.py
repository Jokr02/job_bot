import os
import discord
from discord.ui import Button, View
from dotenv import load_dotenv
from core.jobs import save_job
from core.logging import logger

load_dotenv()

DISCORD_CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID", "0"))

# UI-Komponente für Jobnachrichten
class JobActionsView(View):
    def __init__(self, job):
        super().__init__(timeout=None)
        self.job = job

    @discord.ui.button(label="💾 Save", style=discord.ButtonStyle.green)
    async def save_button(self, interaction: discord.Interaction, button: Button):
        save_job(self.job)
        await interaction.response.send_message("✅ Job gespeichert!", ephemeral=True)

async def send_job_to_discord(job):
    try:
        client = discord.Client(intents=discord.Intents.default())
        await client.login(os.getenv("DISCORD_BOT_TOKEN"))

        channel = await client.fetch_channel(DISCORD_CHANNEL_ID)

        embed = discord.Embed(
            title=job["title"],
            description=f"📍 {job['location']} \n🏢 {job['company']}",
            url=job["url"],
            color=discord.Color.blue()
        )
        embed.set_footer(text="JobBot")

        await channel.send(embed=embed, view=JobActionsView(job))
        await client.close()

    except Exception as e:
        logger.exception(f"Fehler beim Senden der Jobnachricht: {e}")
