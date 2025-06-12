
import discord
from discord import app_commands
from core.jobs import search_jobs
from core.logging import logger, send_error_to_webhook

def register_job_commands(tree):
    @tree.command(name="search_jobs_days", description="Suche Jobs der letzten X Tage")
    @app_commands.describe(tage="Tage zurück (z. B. 14)")
    async def search_jobs_days(interaction: discord.Interaction, tage: int):
        await interaction.response.defer(ephemeral=True)
        try:
            await search_jobs(days=tage)
            await interaction.followup.send(f"🔍 Suche nach Jobs in den letzten {tage} Tagen gestartet.", ephemeral=True)
        except Exception as e:
            logger.error(f"Fehler bei /search_jobs_days: {e}")
            send_error_to_webhook(f"Fehler bei /search_jobs_days: {e}")
