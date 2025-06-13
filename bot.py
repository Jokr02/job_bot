from datetime import datetime
import psutil
import platform
import smtplib
import openai
import os
from email.message import EmailMessage
from fpdf import FPDF
from pathlib import Path
from discord.ui import View, Button, Select
import re 


openai.api_key = os.getenv("OPENAI_API_KEY")


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
from discord import app_commands, Interaction
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

def save_config(config: dict):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)

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

def send_job_to_webhook(message: str):
    job_url = os.getenv("JOB_WEBHOOK_URL")
    if job_url:
        try:
            requests.post(job_url, json={"content": message})
        except Exception as e:
            logger.error(f"Fehler beim Senden an JOB_WEBHOOK_URL: {e}")



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
kununu_cache = {}
def fetch_kununu_rating(company_name):
    if company_name in kununu_cache:
        return kununu_cache[company_name]

    try:
        url = f"https://www.kununu.com/de/suche?term={company_name}"
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")

        # Versuche, Link zur Unternehmensseite zu finden
        first_result = soup.select_one("a.sc-1f9313aa-0")
        if not first_result:
            logger.info(f"⚠️ Kein Kununu-Treffer für {company_name}")
            kununu_cache[company_name] = None
            return None

        company_url = f"https://www.kununu.com{first_result['href']}"
        rating_page = requests.get(company_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        rating_soup = BeautifulSoup(rating_page.text, "html.parser")
        rating_el = rating_soup.select_one("span[data-test='score-box-OverallScore']")

        if rating_el:
            score = rating_el.text.strip()
            result = f"Kununu-Rating: ⭐ {score}/5"
            kununu_cache[company_name] = result
            return result
        else:
            logger.info(f"⚠️ Kein Rating-Element für {company_name}")
            kununu_cache[company_name] = None
            return None
    except Exception as e:
        logger.warning(f"Kununu-Fehler für {company_name}: {e}")
        return None

def normalize_company_name(name: str) -> str:
    # Entfernt Zusätze wie "GmbH", "AG", "KG", "mbH" usw.
    return re.sub(r"\b(gmbh|ag|kg|mbh|inc|ltd)\b", "", name, flags=re.IGNORECASE).strip()

def fetch_raw_job_text(url: str) -> str:
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        candidates = soup.find_all(["p", "div", "section"])
        raw_text = "\n".join(elem.get_text(separator=" ", strip=True) for elem in candidates)
        return raw_text.strip()[:5000]
    except Exception as e:
        return ""

from openai import OpenAI

client = OpenAI()  # lädt automatisch den Key aus OPENAI_API_KEY

def summarize_with_gpt(text: str) -> str:
    if not text:
        return "Keine Beschreibung gefunden."
    try:
        response = client.chat.completions.create(
            model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
            messages=[
                {"role": "system", "content": (
                    "Analysiere die folgende Jobanzeige und gib eine strukturierte Zusammenfassung aus.\n"
                    "Fasse die folgenden drei Punkte möglichst prägnant zusammen:\n\n"
                    "1. Welche Aufgaben/Tätigkeiten sind gefordert?\n"
                    "2. Welche Qualifikationen oder Anforderungen werden erwartet?\n"
                    "3. Was lässt sich über das Unternehmen sagen (wenn Infos vorhanden sind)?\n\n"
                    "Gib die Antwort als gegliederte Liste mit kurzen, verständlichen Sätzen aus."
                )},
                {"role": "user", "content": text}
            ],
            temperature=0.4,
            max_tokens=350
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Zusammenfassung fehlgeschlagen:\n{e}"


def generate_job_pdf(job):
    try:
        # Versuche, direkt Beschreibung zu finden
        response = requests.get(job["url"], headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        desc = soup.select_one(".job-description") or soup.select_one("#job-description")

        if desc:
            description = desc.get_text("\n", strip=True)
        else:
            raw_text = fetch_raw_job_text(job["url"])
            description = summarize_with_gpt(raw_text)

    except Exception as e:
        description = f"Fehler beim Abrufen: {e}"

    # Speichere PDF unter /opt/discord-jobbot/saved_pdfs/
    output_dir = Path("/opt/discord-jobbot/saved_pdfs")
    output_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = output_dir / f"{job['id']}_export.pdf"

    # PDF-Erstellung
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, job["title"], ln=True)
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, f"Unternehmen: {job.get('company', 'Unbekannt')}", ln=True)
    pdf.cell(0, 10, f"Ort: {job.get('location', 'Unbekannt')}", ln=True)
    pdf.multi_cell(0, 8, f"\nLink: {job['url']}\n\nBeschreibung:\n{description}")

    pdf.output(str(pdf_path))
    return str(pdf_path)

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, job["title"], ln=True)
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, f"Unternehmen: {job.get('company', 'Unbekannt')}", ln=True)
    pdf.cell(0, 10, f"Ort: {job.get('location', 'Unbekannt')}", ln=True)
    pdf.multi_cell(0, 8, f"\nLink: {job['url']}\n\nBeschreibung:\n{description}")

    pdf_path = f"/opt/discord-jobbot/saved_pdfs/{job['id']}_export.pdf"
    pdf.output(pdf_path)
    return pdf_path

# -------- Discord UI Buttons --------

class FavoriteActionsView(View):
    def __init__(self, job):
        super().__init__(timeout=None)
        self.job = job

        # Bewerbung senden nur, wenn E-Mail existiert
        if job.get("email"):
            self.add_item(self.PrepareButton())

        self.add_item(FavoriteActionsView.ExportPdfButton())
        self.add_item(self.RemoveButton())

    class PrepareButton(Button):
        def __init__(self):
            super().__init__(label="📄 Bewerbung vorbereiten", style=discord.ButtonStyle.blurple)

        async def callback(self, interaction: discord.Interaction):
            view = self.view  # type: FavoriteActionsView
            job = view.job
            email = job.get("email")

            pdf_path = generate_dynamic_pdf(job["title"])

            files = []
            summary = f"📄 **Bewerbungsvorschau**\n\n"
            summary += f"**Jobtitel:** {job['title']}\n"
            summary += f"**Unternehmen:** {job.get('company', 'Unbekannt')}\n"
            summary += f"**Empfänger:** {email}\n"
            summary += f"**Dateien:**\n"

            for fname in ["lebenslauf.pdf", "zeugnisse.pdf", pdf_path]:
                if fname and os.path.exists(fname):
                    summary += f"- 📎 {fname}\n"
                    with open(fname, "rb") as f:
                        discord_file = discord.File(f, filename=os.path.basename(fname))
                        files.append(discord_file)
                else:
                    summary += f"- ⚠️ {fname} nicht gefunden\n"

            class FinalSendView(View):
                @discord.ui.button(label="📤 Final senden", style=discord.ButtonStyle.green)
                async def confirm_send(self, confirm_interaction: discord.Interaction, button: Button):
                    success = send_application_email(email, job["title"])
                    if success:
                        await confirm_interaction.response.send_message("✅ Bewerbung gesendet.", ephemeral=True)
                    else:
                        await confirm_interaction.response.send_message("❌ Fehler beim Versand.", ephemeral=True)

            await interaction.response.send_message(content=summary, files=files, view=FinalSendView(), ephemeral=True)

    class RemoveButton(Button):
        def __init__(self):
            super().__init__(label="❌ Entfernen", style=discord.ButtonStyle.red)

        async def callback(self, interaction: discord.Interaction):
            view = self.view  # type: FavoriteActionsView
            jobs = load_saved_jobs()
            jobs = [j for j in jobs if j.get("id") != view.job.get("id")]
            with open(SAVED_JOBS_FILE, "w") as f:
                json.dump(jobs, f, indent=2)
            await interaction.response.send_message("🗑️ Job entfernt.", ephemeral=True)
    class ExportPdfButton(Button):
        def __init__(self):
            super().__init__(label="📄 PDF exportieren", style=discord.ButtonStyle.secondary)

        async def callback(self, interaction: discord.Interaction):
            await interaction.response.defer(ephemeral=True)  # sofortige Antwort, hält Interaktion offen

            job = self.view.job
            path = generate_job_pdf(job)

            if os.path.exists(path):
                file = discord.File(path, filename=os.path.basename(path))
                await interaction.followup.send("📄 Hier ist dein Jobexport:", file=file, ephemeral=True)
            else:
                await interaction.followup.send("❌ PDF konnte nicht erstellt werden.", ephemeral=True)

class WorkTypeSelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Alle", value="all", description="Keine Einschränkung (Standard)"),
            discord.SelectOption(label="Vor Ort", value="onsite"),
            discord.SelectOption(label="Hybrid", value="hybrid"),
            discord.SelectOption(label="Home Office", value="remote")
        ]

        super().__init__(placeholder="Arbeitsmodell wählen...", options=options)

    async def callback(self, interaction: Interaction):
        selected = self.values[0]
        config = load_config()

        # Lege bei "all" trotzdem leeren String in config ab
        config["work_type"] = "" if selected == "all" else selected
        save_config(config)

        label = "Alle" if selected == "all" else selected.capitalize()
        await interaction.response.send_message(f"✅ Arbeitsmodell gespeichert: **{label}**", ephemeral=True)



class WorkTypeView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(WorkTypeSelect())



class JobActionsView(View):
    def __init__(self, job):
        super().__init__(timeout=None)
        self.job = job

    @discord.ui.button(label="💾 Save", style=discord.ButtonStyle.green)
    async def save_button(self, interaction: discord.Interaction, button: Button):
        save_job(self.job)
        await interaction.response.send_message("✅ Job gespeichert!", ephemeral=True)



def fetch_jobs_ihk(keywords, location):
    jobs = []
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        for kw in keywords:
            suchtext = urllib.parse.quote(kw)
            ort = urllib.parse.quote(location)
            url = f"https://www.ihk-lehrstellenboerse.de/suche?suchtext={suchtext}&umkreis=100&ort={ort}"

            r = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(r.text, "html.parser")

            for listing in soup.select(".resultList__item")[:3]:
                title = listing.select_one(".resultList__title")
                firm = listing.select_one(".resultList__firm")
                loc = listing.select_one(".resultList__location")
                href = title["href"] if title and title.has_attr("href") else "#"

                jobs.append({
                    "title": title.get_text(strip=True) if title else kw,
                    "company": firm.get_text(strip=True) if firm else "IHK",
                    "location": loc.get_text(strip=True) if loc else location,
                    "url": f"https://www.ihk-lehrstellenboerse.de{href}",
                    "source": "IHK-Lehrstellenbörse"
                })
    except Exception as e:
        logger.error(f"IHK Scraping-Fehler: {e}")
        send_error_to_webhook(f"IHK Scraping-Fehler: {e}")
    return jobs



def fetch_jobs_honeypot(keywords):
    jobs = []
    url = "https://www.honeypot.io/jobs"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        r = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")

        found = 0
        for listing in soup.select("a[href^='/job/']"):
            title = listing.get_text(strip=True)
            if any(kw.lower() in title.lower() for kw in keywords):
                jobs.append({
                    "title": title,
                    "company": "Honeypot",
                    "location": "Remote / EU",
                    "url": f"https://www.honeypot.io{listing['href']}",
                    "source": "Honeypot"
                })
                found += 1
            if found >= 3:
                break
    except Exception as e:
        logger.error(f"Honeypot Scraping-Fehler: {e}")
        send_error_to_webhook(f"Honeypot Scraping-Fehler: {e}")
    return jobs




async def search_jobs(days: int = 10):
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
            send_error_to_webhook(f"Adzuna Fehler: {e}")

    # -------- Agentur --------
    agentur_jobs = fetch_jobs_agentur(keywords, config["location"])
    all_jobs.extend(agentur_jobs)

    # -------- Honeypot & IHK --------
    all_jobs += fetch_jobs_honeypot(keywords)
    all_jobs += fetch_jobs_ihk(keywords, config["location"])

    if not all_jobs:
        logger.info("Keine neuen Jobs gefunden.")
        return

    save_seen_jobs(seen_ids)

    # -------- An Discord-Channel senden --------
    try:
        channel = await bot.fetch_channel(CHANNEL_ID)
        for job in all_jobs:
            desc = f"💼 **{highlight_keywords(job['title'], keywords)}**\n🏢 {job['company']}\n📍 {job['location']}\n🔗 {job['url']}"
            
            # Kununu-Rating versuchen (alle Quellen!)
            company_clean = normalize_company_name(job['company'])
            kununu = fetch_kununu_rating(normalize_company_name(job['company'])) if job.get('company') else None
            if kununu:
                desc += f"\n✨ {kununu}"

            await channel.send(desc, view=JobActionsView(job))

    except Exception as e:
        logger.error(f"Fehler beim Senden an Discord: {e}")
        send_error_to_webhook(f"Fehler beim Senden an Discord: {e}")

@tree.command(name="favorites", description="Zeigt gespeicherte Jobs an")
async def favorites(interaction: discord.Interaction):
    jobs = load_saved_jobs()
    if not jobs:
        await interaction.response.send_message("📭 Keine gespeicherten Jobs gefunden.", ephemeral=True)
        return

    # Jobs anzeigen
    for job in jobs[-10:]:  # Zeige max. 10 letzte
        embed = discord.Embed(
            title=job["title"],
            description=f"🏢 {job.get('company', 'Unbekannt')}",
            color=0x00ff00
        )
        embed.add_field(name="Ort", value=job.get("location", "Unbekannt"), inline=True)
        embed.add_field(name="Link", value=job.get("url", "Kein Link"), inline=False)

        await interaction.channel.send(embed=embed, view=FavoriteActionsView(job))

    await interaction.response.send_message("✅ Favoriten angezeigt.", ephemeral=True)


@tree.command(name="update_config", description="Aktualisiert Suchparameter für Jobs")
@app_commands.describe(
    location="Ort der Jobsuche",
    radius="Suchradius in Kilometern",
    keywords="Kommagetrennte Keywords (z. B. linux, vmware)"
)
async def update_config(interaction: discord.Interaction, location: str, radius: int, keywords: str):
    config = load_config()
    config["location"] = location
    config["radius"] = radius
    config["keywords"] = [kw.strip() for kw in keywords.split(",")]

    save_config(config)

    response = f"✅ Konfiguration aktualisiert!\n\n" \
               f"📍 Ort: `{location}`\n" \
               f"📏 Radius: `{radius} km`\n" \
               f"🔎 Keywords: `{', '.join(config['keywords'])}`"

    await interaction.response.send_message(response, ephemeral=True)


@tree.command(name="clear_favorites", description="Löscht alle gespeicherten Jobs")
async def clear_favorites(interaction: discord.Interaction):
    clear_saved_jobs()
    await interaction.response.send_message("🧹 Alle gespeicherten Jobs wurden gelöscht.", ephemeral=True)

@tree.command(name="config", description="Zeigt aktuelle Konfiguration")
async def zeige_config(interaction: discord.Interaction):
    config = load_config()
    text = f"🌍 Ort: {config['location']}\n📏 Radius: {config['radius']} km\n🔎 Keywords: {', '.join(config['keywords'])}\n⏰ Uhrzeit: {config['execution_time']}\nOrt: {config['work_type']}"
    await interaction.response.send_message(text, ephemeral=True)



@tree.command(name="set_time", description="Setzt die Uhrzeit für tägliche Suche (z.B. 12:00)")
@app_commands.describe(uhrzeit="Format: HH:MM (24h)")
async def set_time(interaction: discord.Interaction, uhrzeit: str):
    await interaction.response.defer(ephemeral=True)
    try:
        datetime.strptime(uhrzeit, "%H:%M")
        config = load_config()
        config["execution_time"] = uhrzeit
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=2)

        global daily_search_task
        if daily_search_task:
            daily_search_task.cancel()

        daily_search_task = asyncio.create_task(schedule_daily_search())

        await interaction.followup.send(f"⏰ Neue Uhrzeit gesetzt: {uhrzeit} – tägliche Suche wurde neu eingeplant.", ephemeral=True)
    except ValueError:
        await interaction.followup.send("❌ Ungültiges Format. Bitte HH:MM verwenden (z. B. 08:30)", ephemeral=True)
@tree.command(name="send_testmail", description="Sendet eine Testbewerbung an eine E-Mail-Adresse")
@app_commands.describe(email="Zieladresse für die Test-E-Mail")
async def send_testmail(interaction: discord.Interaction, email: str):
    await interaction.response.defer(ephemeral=True)

    success = send_application_email(email, "Test-Job IT Support")

    message = f"✅ Testmail gesendet an {email}" if success else "❌ Fehler beim Versand der Testmail."
    await interaction.followup.send(message, ephemeral=True)


@tree.command(name="search_jobs_days", description="Sucht Jobs der letzten x Tage", guild=discord.Object(id=1380610208602001448))
@app_commands.describe(tage="Anzahl der letzten Tage")
async def search_jobs_days(interaction: discord.Interaction, tage: int):
    await interaction.response.defer(ephemeral=True)
    try:
        await search_jobs(days=tage)
        await interaction.followup.send(f"🔎 Jobsuche (letzte {tage} Tage) wurde gestartet.", ephemeral=True)
    except Exception as e:
        logger.error(f"Fehler bei /search_jobs_days: {e}")
        send_error_to_webhook(f"Fehler bei /search_jobs_days: {e}")

class JobDaysSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Letzter Tag", value="1", description="Jobs der letzten 1 Tage"),
            discord.SelectOption(label="Letzte 3 Tage", value="3", description="Jobs der letzten 3 Tage"),
            discord.SelectOption(label="Letzte 7 Tage", value="7", description="Jobs der letzten 7 Tage"),
            discord.SelectOption(label="Letzte 14 Tage", value="14", description="Jobs der letzten 14 Tage")
        ]
        super().__init__(placeholder="Wähle Zeitraum für Jobsuche...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        tage = int(self.values[0])
        await interaction.response.defer(ephemeral=True)
        try:
            await search_jobs(days=tage)
            await interaction.followup.send(f"🔎 Jobsuche für die letzten {tage} Tage wurde gestartet.", ephemeral=True)
        except Exception as e:
            logger.error(f"Fehler bei Dropdown-Jobsuche: {e}")
            send_error_to_webhook(f"Fehler bei Dropdown-Jobsuche: {e}")
            await interaction.followup.send("❌ Fehler bei der Jobsuche.", ephemeral=True)


class JobDaysView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)
        self.add_item(JobDaysSelect())


@tree.command(name="search_jobs_dropdown", description="Starte Jobsuche per Auswahl der Tage", guild=discord.Object(id=1380610208602001448))
async def search_jobs_dropdown(interaction: discord.Interaction):
    await interaction.response.send_message("Bitte wähle den Zeitraum für die Jobsuche:", view=JobDaysView(), ephemeral=True)

@tree.command(name="update_work_type", description="Wähle das Arbeitsmodell (remote, hybrid, onsite)")
async def update_work_type(interaction: Interaction):
    await interaction.response.send_message(
        "Bitte wähle dein gewünschtes Arbeitsmodell:",
        view=WorkTypeView(),
        ephemeral=True
    )


@bot.event

async def cleanup_old_messages():
    try:
        channel = await bot.fetch_channel(CHANNEL_ID)
        from datetime import timezone
        cutoff = datetime.now(timezone.utc) - timedelta(days=30)

        deleted = 0
        async for message in channel.history(limit=100):
            if message.author == bot.user and message.created_at < cutoff:
                await message.delete()
                deleted += 1
        if deleted:
            logger.info(f"🧹 {deleted} alte Nachrichten gelöscht.")
            if ERROR_WEBHOOK_URL:
                requests.post(ERROR_WEBHOOK_URL, json={"content": f"🧹 {deleted} alte Bot-Nachrichten im Channel gelöscht."})
    except Exception as e:
        logger.error(f"Fehler beim Aufräumen alter Nachrichten: {e}")
        send_error_to_webhook(f"Fehler beim Aufräumen alter Nachrichten: {e}")

@bot.event
async def on_ready():
    logger.info(f"✅ Eingeloggt als {bot.user}")
    await tree.sync()

    # ------------------- Bot-Startmeldung nur einmal -------------------
    if ERROR_WEBHOOK_URL:
        try:
            bot_version = '1.0.0'
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ram_total = round(psutil.virtual_memory().total / (1024**3), 2)
            ram_used = round(psutil.virtual_memory().used / (1024**3), 2)
            hostname = platform.node()
            sysinfo = f"**Version:** {bot_version}\n**Zeit:** {timestamp}\n**System:** {hostname}\n**RAM:** {ram_used}/{ram_total} GB"
            msg = f"✅ JobBot gestartet als **{bot.user}**\n{sysinfo}"
            requests.post(ERROR_WEBHOOK_URL, json={"content": msg})
        except Exception as e:
            logger.error(f"Fehler beim erweiterten Healthcheck: {e}")

    # Optional zweite einfache Meldung (entweder oder)
    #if ERROR_WEBHOOK_URL:
    #    try:
    #        requests.post(ERROR_WEBHOOK_URL, json={"content": f"✅ JobBot gestartet und verbunden als **{bot.user}**"})
    #    except Exception as e:
    #        logger.error(f"Fehler beim Healthcheck-Webhook: {e}")
    
    await tree.sync()
# Starte täglichen Bereinigungs-Task
    async def cleanup_loop():
        await bot.wait_until_ready()
        while not bot.is_closed():
            try:
                await cleanup_old_messages()
            except Exception as e:
                logger.error(f"Fehler in cleanup_loop: {e}")
                send_error_to_webhook(f"Fehler in cleanup_loop: {e}")
            await asyncio.sleep(86400)  # 24h warten

    bot.loop.create_task(cleanup_loop())
    await cleanup_old_messages()
# Starte wiederkehrende Jobsuche jede Stunde
    async def hourly_job_loop():
        await bot.wait_until_ready()
        while not bot.is_closed():
            try:
                await search_jobs()
            except Exception as e:
                logger.error(f"Fehler im stündlichen Job-Loop: {e}")
                send_error_to_webhook(f"Fehler im Jobloop: {e}")
            await asyncio.sleep(3600)  # 1 Stunde warten

    bot.loop.create_task(hourly_job_loop())
    
    await schedule_daily_search()
    
async def schedule_daily_search():
    await bot.wait_until_ready()
    while not bot.is_closed():
        try:
            config = load_config()
            target_time = datetime.strptime(config["execution_time"], "%H:%M").time()
            now = datetime.now()
            next_run = datetime.combine(now.date(), target_time)

            if now.time() > target_time:
                next_run += timedelta(days=1)

            wait_seconds = (next_run - now).total_seconds()
            await asyncio.sleep(wait_seconds)
            await search_jobs()
        except Exception as e:
            logger.error(f"Fehler bei geplanter Suche: {e}")
            send_error_to_webhook(f"Fehler bei geplanter Suche: {e}")
        await asyncio.sleep(86400)


# -------- Bot starten --------
bot.run(TOKEN)



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

from discord import app_commands
from discord.ext import commands

@tree.command(name="clear_chat", description="Löscht alle Jobbot-Nachrichten im aktuellen Kanal")
@app_commands.checks.has_permissions(manage_messages=True)
async def clear_chat(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)

    def is_bot_message(msg):
        return msg.author == interaction.client.user

    deleted = await interaction.channel.purge(limit=100, check=is_bot_message)
    await interaction.followup.send(f"🧹 {len(deleted)} Jobbot-Nachrichten wurden gelöscht.", ephemeral=True)
