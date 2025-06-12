
from discord.ui import View, Button
import discord
from core.emailer import send_application_email
from core.config_utils import load_saved_jobs, save_job
import json
import os

SAVED_JOBS_FILE = "saved_jobs.json"

class FavoriteActionsView(View):
    def __init__(self, job):
        super().__init__(timeout=None)
        self.job = job

    @discord.ui.button(label="✅ Bewerbung senden", style=discord.ButtonStyle.green)
    async def send_button(self, interaction: discord.Interaction, button: Button):
        if not self.job.get("email"):
            await interaction.response.send_message("❌ Keine E-Mail-Adresse verfügbar.", ephemeral=True)
            return
        success = send_application_email(self.job["email"], self.job["title"], attachments=["anschreiben.pdf", "zeugnisse.pdf"])
        if success:
            await interaction.response.send_message("📤 Bewerbung erfolgreich versendet!", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Fehler beim Versand der Bewerbung.", ephemeral=True)

    @discord.ui.button(label="❌ Entfernen", style=discord.ButtonStyle.red)
    async def remove_button(self, interaction: discord.Interaction, button: Button):
        jobs = load_saved_jobs()
        jobs = [j for j in jobs if j.get("id") != self.job.get("id")]
        with open(SAVED_JOBS_FILE, "w") as f:
            json.dump(jobs, f, indent=2)
        await interaction.response.send_message("🗑️ Job entfernt.", ephemeral=True)
