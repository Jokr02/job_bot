# Kein @tree.command vor cleanup_old_messages gefunden – Datei blieb unverändert.
from datetime import datetime, timezone
import psutil
import platform
import smtplib
from email.message import EmailMessage
from fpdf import FPDF

def generate_dynamic_pdf(job_title):
    try:
        with open("anschreiben_vorlage.txt", "r", encoding="utf-8") as f:
            text = f.read()
            text = text.replace("{{job_title}}", job_title)
            text = text.replace("{{sender_name}}", os.getenv("SENDER_NAME", "Max Mustermann"))

        pdf_path = f"anschreiben_{job_title}.pdf"
        pdf = FPDF()
        pdf.add_page()

        paragraphs = text.strip().split("\n\n")
        title = paragraphs[0]
        rest = paragraphs[1:]

        # Title bold, size 11
        pdf.set_font("Arial", style="B", size=11)
        pdf.multi_cell(0, 6, title)
        pdf.ln(4)

        # Body regular, size 11
        pdf.set_font("Arial", size=11)
        for paragraph in rest:
            for line in paragraph.split("\n"):
                pdf.multi_cell(0, 6, line)
            pdf.ln(4)

        pdf.output(pdf_path)
        return pdf_path
    except Exception as e:
        logger.error(f"Fehler beim Generieren des PDFs: {e}")
        return None
def send_application_email(to_address, job_title):
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASSWORD")
    sender_name = os.getenv("SENDER_NAME", "JobBot")
    sender_email = smtp_user

    msg = EmailMessage()
    msg["Subject"] = f"Bewerbung: {job_title}"
    msg["From"] = f"{sender_name} <{sender_email}>"
    msg["To"] = to_address
    msg.set_content(f"Sehr geehrte Damen und Herren,\n\nhiermit bewerbe ich mich auf die Stelle '{job_title}'.\nIm Anhang finden Sie meine Unterlagen.\n\nMit freundlichen Grüßen\n{sender_name}")

    # Anhänge
    pdf = generate_dynamic_pdf(job_title)
    files = ["lebenslauf.pdf", "zeugnisse.pdf"]
    if pdf:
        files.append(pdf)

    for filename in files:
        if os.path.exists(filename):
            with open(filename, "rb") as f:
                msg.add_attachment(f.read(), maintype="application", subtype="pdf", filename=os.path.basename(filename))

    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
        return True
    except Exception as e:
        logger.error(f"E-Mail-Sendeproblem: {e}")
        return False


import os
import json
import re
import logging
import asyncio
import urllib.parse
import requests
from datetime import datetime, timezone, timedelta
from logging.handlers import TimedRotatingFileHandler
from zoneinfo import ZoneInfo
from bs4 import BeautifulSoup

import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Button
from dotenv import load_dotenv

# -------- Logging --------
os.makedirs("logs", exist_ok=True)
logger = logging.getLogger("jobbot")
logger.setLevel(logging.INFO)
handler = TimedRotatingFileHandler("logs/jobbot.log", when="midnight", backupCount=7, encoding="utf-8")
formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.addHandler(logging.StreamHandler())

# -------- Environment Variables --------
load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))
APP_ID = os.getenv("ADZUNA_APP_ID")
APP_KEY = os.getenv("ADZUNA_APP_KEY")
COUNTRY = os.getenv("ADZUNA_COUNTRY", "de")
ERROR_WEBHOOK_URL = os.getenv("ERROR_WEBHOOK_URL")

CONFIG_FILE = "config.json"
JOBS_SEEN_FILE = "jobs_seen.json"
SAVED_JOBS_FILE = "saved_jobs.json"

# -------- Discord Setup --------
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree
daily_search_task = None  # Scheduled job task
# -------- Helper Functions --------
def load_config():
    if not os.path.exists(CONFIG_FILE):
        default = {"location": "Coburg", "radius": 100, "keywords": ["system administrator"], "work_type": "all", "execution_time": "12:00"}
        with open(CONFIG_FILE, "w") as f:
            json.dump(default, f, indent=2)
    with open(CONFIG_FILE) as f:
        return json.load(f)

def load_seen_jobs():
    if not os.path.exists(JOBS_SEEN_FILE):
        with open(JOBS_SEEN_FILE, "w") as f:
            json.dump({"posted_ids": []}, f)
    with open(JOBS_SEEN_FILE) as f:
        return set(json.load(f)["posted_ids"])

def save_seen_jobs(job_ids):
    with open(JOBS_SEEN_FILE, "w") as f:
        json.dump({"posted_ids": list(job_ids)}, f, indent=2)

def save_job(job):
    jobs = []
    if os.path.exists(SAVED_JOBS_FILE):
        with open(SAVED_JOBS_FILE) as f:
            jobs = json.load(f)
    jobs.append(job)
    with open(SAVED_JOBS_FILE, "w") as f:
        json.dump(jobs, f, indent=2)

def load_saved_jobs():
    if os.path.exists(SAVED_JOBS_FILE):
        with open(SAVED_JOBS_FILE) as f:
            return json.load(f)
    return []

def clear_saved_jobs():
    with open(SAVED_JOBS_FILE, "w") as f:
        json.dump([], f)


def send_error_to_webhook(error_text):
    if ERROR_WEBHOOK_URL:
        try:
            requests.post(ERROR_WEBHOOK_URL, json={"content": f"🚨 Bot Error:\n```{error_text}```"})
        except Exception as e:
            logger.error(f"Fehler beim Senden an Webhook: {e}")



def fetch_jobs_agentur(keywords, location):
    jobs = []
    for kw in keywords:
        q = urllib.parse.quote(kw)
        url = f"https://jobboerse.arbeitsagentur.de/vamJB/start?aa=1&ref=home&stellenart=1&was={q}&wo={location}"
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            r = requests.get(url, headers=headers, timeout=20)
            soup = BeautifulSoup(r.text, "html.parser")
            for joblink in soup.select("a.stellenangebot")[:3]:
                title = joblink.text.strip()
                href = joblink["href"]
                jobs.append({
                    "title": title,
                    "company": "Arbeitsagentur",
                    "location": location,
                    "url": f"https://jobboerse.arbeitsagentur.de{href}",
                    "source": "Agentur für Arbeit"
                })
        except Exception as e:
            logger.error(f"Agentur fetch error: {e}")
            send_error_to_webhook(f"Arbeitsagentur error: {e}")
    return jobs


def highlight_keywords(text, keywords):
    for kw in sorted(keywords, key=len, reverse=True):
        text = re.sub(rf"(?i)\\b({re.escape(kw)})\\b", r"**\\1**", text)
    return text

def fetch_kununu_rating(company_name):
    try:
        base_url = "https://www.kununu.com"
        query = urllib.parse.quote(company_name)
        search_url = f"{base_url}/de/suche?query={query}"
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(search_url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")

        profile_link = soup.select_one("a[data-test='search-result-link']")
        if not profile_link:
            return None

        kununu_url = base_url + profile_link["href"]
        profile_resp = requests.get(kununu_url, headers=headers, timeout=10)
        profile_soup = BeautifulSoup(profile_resp.text, "html.parser")
        rating_el = profile_soup.select_one("div[data-test='score-value']")

        if not rating_el:
            return None

        rating = rating_el.text.strip()
        return f"{rating} ⭐ – {kununu_url}"
    except Exception as e:
        logger.warning(f"Kununu fetch failed: {e}")
        return None

# -------- Discord UI Buttons --------

class FavoriteActionsView(View):
    def __init__(self, job):
        super().__init__(timeout=None)
        self.job = job

    @discord.ui.button(label="✅ Bewerbung senden", style=discord.ButtonStyle.green)
    async def send_button(self, interaction: discord.Interaction, button: Button):
        if not self.job.get("email"):
            await interaction.response.send_message("❌ Keine E-Mail-Adresse verfügbar.", ephemeral=True)
            return
        success = send_application_email(self.job["email"], self.job["title"])
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

        super().__init__(timeout=None)
        self.job = job

    @discord.ui.button(label="💾 Save", style=discord.ButtonStyle.green)
    async def save_button(self, interaction: discord.Interaction, button: Button):
        save_job(self.job)
        await interaction.response.send_message("✅ Job saved!", ephemeral=True)

    @discord.ui.button(label="⏭️ Skip", style=discord.ButtonStyle.grey)
    async def skip_button(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message("⏩ Skipped.", ephemeral=True)

        params = {
            "query": kw,
            "location": config["location"],
            "radius": config["radius"],
            "limit": 3
        }
        try:
            data = r.json()
            for job in data.get("jobs", []):
                job_id = job.get("id")
                if job_id in seen_ids:
                    continue
                job_obj = {
                    "id": job_id,
                    "title": job.get("title"),
                    "company": job.get("company", {}).get("name"),
                    "location": job.get("location", {}).get("name"),
                    "url": job.get("link")
                }
                jobs.append(job_obj)
                seen_ids.add(job_id)
        except Exception as e:
            logger.warning(f"Joblift Fehler: {e}")

def fetch_jobs_ihk():
    # Optional: Scraping der IHK-Seiten – hier Dummy
    return []

def fetch_jobs_honeypot():
    # Optional: Scraping von Honeypot.io – hier Dummy
    return []

async def search_jobs(days: int = 1):
    config = load_config()
    keywords = config["keywords"]
    seen_ids = load_seen_jobs()
    all_jobs = []

    # -------- Adzuna --------
    for kw in keywords:
        url = f"https://api.adzuna.com/v1/api/jobs/{COUNTRY}/search/1"
        params = {
            "app_id": APP_ID,
            "app_key": APP_KEY,
            "results_per_page": 3,
            "what": kw,
            "where": config["location"],
            "distance": config["radius"],
            "max_days_old": days,
        }
        try:
            r = requests.get(url, params=params, timeout=10)
            data = r.json()
            for job in data.get("results", []):
                job_id = job.get("id")
                if job_id in seen_ids:
                    continue
                job_obj = {
                    "id": job_id,
                    "title": job.get("title"),
                    "company": job.get("company", {}).get("display_name"),
                    "location": job.get("location", {}).get("display_name"),
                    "url": job.get("redirect_url")
                }
                all_jobs.append(job_obj)
                seen_ids.add(job_id)
        except Exception as e:
            logger.error(f"Adzuna Fehler: {e}")

    # -------- Joblift --------

    # -------- Honeypot & IHK (optional) --------
    all_jobs += fetch_jobs_honeypot()
    all_jobs += fetch_jobs_ihk()

    
    agentur_jobs = fetch_jobs_agentur(keywords, config["location"])
    all_jobs.extend(agentur_jobs)
    

    if not all_jobs:
        logger.info("Keine neuen Jobs gefunden.")
        return
        logger.info("Keine neuen Jobs gefunden.")
        return

    save_seen_jobs(seen_ids)

    # -------- An Discord senden --------
    try:
        channel = await bot.fetch_channel(CHANNEL_ID)
        for job in all_jobs:
            desc = f"💼 **{highlight_keywords(job['title'], keywords)}**\n🏢 {job['company']}\n📍 {job['location']}\n🔗 {job['url']}"
            kununu = fetch_kununu_rating(job['company']) if job['company'] else None
            if kununu:
                desc += f"\n✨ {kununu}"
            await channel.send(desc, view=JobView(job))
    except Exception as e:
        logger.error(f"Fehler beim Senden an Discord: {e}")
@tree.command(name="favorites", description="Zeigt gespeicherte Jobs an")

