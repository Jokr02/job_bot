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
from datetime import datetime, timedelta
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
JOBLIFT_API_KEY = os.getenv("JOBLIFT_API_KEY")

CONFIG_FILE = "config.json"
JOBS_SEEN_FILE = "jobs_seen.json"
SAVED_JOBS_FILE = "saved_jobs.json"

# -------- Discord Setup --------
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree
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

    def __init__(self, job):
        super().__init__(timeout=None)
        self.job = job

    @discord.ui.button(label="💾 Save", style=discord.ButtonStyle.green)
    async def save_button(self, interaction: discord.Interaction, button: Button):
        save_job(self.job)
        await interaction.response.send_message("✅ Job saved!", ephemeral=True)

    @discord.ui.button(label="⏭️ Skip", style=discord.ButtonStyle.grey)
    async def skip_button(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message("⏩ Skipped.", ephemeral=True)
def fetch_jobs_joblift(config, seen_ids):
    jobs = []
    if not JOBLIFT_API_KEY:
        logger.warning("Kein JOBLIFT_API_KEY gesetzt.")
        return jobs

    headers = {"Authorization": f"Bearer {JOBLIFT_API_KEY}"}
    for kw in config["keywords"]:
        params = {
            "query": kw,
            "location": config["location"],
            "radius": config["radius"],
            "limit": 3
        }
        try:
            r = requests.get("https://api.joblift.com/v1/search", headers=headers, params=params, timeout=10)
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
    return jobs

def fetch_jobs_ihk():
    # Optional: Scraping der IHK-Seiten – hier Dummy
    return []

def fetch_jobs_honeypot():
    # Optional: Scraping von Honeypot.io – hier Dummy
    return []

async def search_jobs():
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
            "distance": config["radius"]
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
    all_jobs += fetch_jobs_joblift(config, seen_ids)

    # -------- Honeypot & IHK (optional) --------
    all_jobs += fetch_jobs_honeypot()
    all_jobs += fetch_jobs_ihk()

    if not all_jobs:
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
async def favorites(interaction: discord.Interaction):
    jobs = load_saved_jobs()
    if not jobs:
        await interaction.response.send_message("📭 Keine gespeicherten Jobs gefunden.", ephemeral=True)
        return

    msg_lines = []
    for job in jobs[-10:]:
        msg_lines.append(f"💼 **{job['title']}**\n🏢 {job['company']}\n📍 {job['location']}\n🔗 {job['url']}")
    await interaction.response.send_message("\n\n".join(msg_lines), ephemeral=True)

@tree.command(name="update_config", description="Aktualisiert Suchparameter für Jobs")
@app_commands.describe(
    location="Ort der Jobsuche",
    radius="Suchradius in Kilometern",
    keywords="Kommagetrennte Keywords (z. B. linux, vmware)",
    work_type="Arbeitsform: all, remote, hybrid, onsite"
)
async def update_config(interaction: discord.Interaction, location: str, radius: int, keywords: str, work_type: str = "all"):
    config = load_config()
    config["location"] = location
    config["radius"] = radius
    config["keywords"] = [kw.strip() for kw in keywords.split(",")]
    config["work_type"] = work_type
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)
    await interaction.response.send_message("✅ Konfiguration aktualisiert!", ephemeral=True)

    jobs = load_saved_jobs()
    if not jobs:
        await interaction.response.send_message("📭 Keine gespeicherten Jobs gefunden.", ephemeral=True)
        return

    msg_lines = []
    for job in jobs[-10:]:
        msg_lines.append(f"💼 **{job['title']}**\n🏢 {job['company']}\n📍 {job['location']}\n🔗 {job['url']}")
    await interaction.response.send_message("\n\n".join(msg_lines), ephemeral=True)

@tree.command(name="clear_favorites", description="Löscht alle gespeicherten Jobs")
async def clear_favorites(interaction: discord.Interaction):
    clear_saved_jobs()
    await interaction.response.send_message("🧹 Alle gespeicherten Jobs wurden gelöscht.", ephemeral=True)

@tree.command(name="config", description="Zeigt aktuelle Konfiguration")
async def zeige_config(interaction: discord.Interaction):
    config = load_config()
    text = f"🌍 Ort: {config['location']}\n📏 Radius: {config['radius']} km\n🔎 Keywords: {', '.join(config['keywords'])}\n⏰ Uhrzeit: {config['execution_time']}"
    await interaction.response.send_message(text, ephemeral=True)


@tree.command(name="set_parameters", description="Setzt Ort, Radius und Keywords für die Jobsuche")
@app_commands.describe(
    location="Ort der Jobsuche",
    radius="Suchradius in Kilometern",
    keywords="Kommagetrennte Stichwörter (z. B. linux, vmware, windows)"
)
async def set_parameters(interaction: discord.Interaction, location: str, radius: int, keywords: str):
    config = load_config()
    config["location"] = location
    config["radius"] = radius
    config["keywords"] = [k.strip() for k in keywords.split(",")]
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)
    await interaction.response.send_message("✅ Suchparameter wurden aktualisiert.", ephemeral=True)


@tree.command(name="set_time", description="Setzt die Uhrzeit für tägliche Suche (z.B. 12:00)")
@app_commands.describe(uhrzeit="Format: HH:MM (24h)")
async def set_time(interaction: discord.Interaction, uhrzeit: str):
    try:
        datetime.strptime(uhrzeit, "%H:%M")
        config = load_config()
        config["execution_time"] = uhrzeit
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=2)
        if not interaction.response.is_done():
            await interaction.response.send_message(f"⏰ Zeit geändert zu {uhrzeit}.", ephemeral=True)
        else:
            await interaction.followup.send(f"⏰ Zeit geändert zu {uhrzeit}.", ephemeral=True)
    except ValueError:
        if not interaction.response.is_done():
            await interaction.response.send_message("❌ Ungültiges Format. Bitte HH:MM (z.B. 08:30) nutzen.", ephemeral=True)
        else:
            await interaction.followup.send("❌ Ungültiges Format. Bitte HH:MM (z.B. 08:30) nutzen.", ephemeral=True)
async def set_time(interaction: discord.Interaction, uhrzeit: str):
    try:
        datetime.strptime(uhrzeit, "%H:%M")
        config = load_config()
        config["execution_time"] = uhrzeit
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=2)
        await interaction.response.send_message(f"⏰ Zeit geändert zu {uhrzeit}.", ephemeral=True)
    except:
        await interaction.response.send_message("❌ Ungültiges Format. Bitte HH:MM (z.B. 08:30) nutzen.", ephemeral=True)

# -------- Bot-Start & Zeitplanung --------
@tree.command(name="send_testmail", description="Sendet eine Testbewerbung an eine E-Mail-Adresse")
@app_commands.describe(email="Zieladresse für die Test-E-Mail")
async def send_testmail(interaction: discord.Interaction, email: str):
    await interaction.response.defer(ephemeral=True)

    success = send_application_email(email, "Test-Job IT Support")

    message = f"✅ Testmail gesendet an {email}" if success else "❌ Fehler beim Versand der Testmail."
    await interaction.followup.send(message, ephemeral=True)
@bot.event
async def on_ready():
    logger.info(f"✅ Eingeloggt als {bot.user}")
    await tree.sync()
    await schedule_daily_search()

async def schedule_daily_search():
    config = load_config()
    hour, minute = map(int, config.get("execution_time", "12:00").split(":"))
    now = datetime.now(ZoneInfo("Europe/Berlin"))
    target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if target < now:
        target += timedelta(days=1)
    delay = (target - now).total_seconds()
    logger.info(f"⏳ Warten bis {target.strftime('%Y-%m-%d %H:%M:%S %Z')} ({int(delay)}s)")
    await asyncio.sleep(delay)
    await search_jobs()
    while True:
        await asyncio.sleep(86400)
        await search_jobs()

# -------- Bot starten --------
bot.run(TOKEN)



@tree.command(name="favorites", description="Zeigt gespeicherte Jobs mit Buttons")
async def favorites(interaction: discord.Interaction):
    jobs = load_saved_jobs()
    if not jobs:
        await interaction.response.send_message("📭 Keine gespeicherten Jobs gefunden.", ephemeral=True)
        return

    for job in jobs:
        embed = discord.Embed(title=job["title"], description=f"{job.get("company", "")}", color=0x00ff00)
        embed.add_field(name="Ort", value=job.get("location", ""), inline=True)
        embed.add_field(name="Link", value=job.get("url", ""), inline=False)
        await interaction.channel.send(embed=embed, view=FavoriteActionsView(job))
    await interaction.response.send_message("✅ Favoriten geladen.", ephemeral=True)
