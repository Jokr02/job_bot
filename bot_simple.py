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

load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")

CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))
ADZUNA_APP_ID = os.getenv("ADZUNA_APP_ID")
ADZUNA_APP_KEY = os.getenv("ADZUNA_APP_KEY")
COUNTRY = os.getenv("ADZUNA_COUNTRY", "de")

CONFIG_FILE = "config.json"
SEEN_FILE = "jobs_seen.json"

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree


def load_config():
    with open(CONFIG_FILE) as f:
        return json.load(f)

def load_seen():
    if not os.path.exists(SEEN_FILE):
        return set()
    with open(SEEN_FILE) as f:
        return set(json.load(f))

def save_seen(ids):
    with open(SEEN_FILE, "w") as f:
        json.dump(list(ids), f)
def fetch_kununu_rating(company_name):
    import re
    from bs4 import BeautifulSoup

    def clean_name(name):
        return re.sub(r"\b(gmbh|mbh|ag|kg|se|inc|ltd)\b", "", name, flags=re.IGNORECASE).strip()

    try:
        name = clean_name(company_name)
        url = f"https://www.kununu.com/de/suche?term={name}"
        headers = {"User-Agent": "Mozilla/5.0"}
        search_response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(search_response.text, "html.parser")

        link = soup.select_one("a.sc-1f9313aa-0")
        if not link:
            return None

        detail_url = f"https://www.kununu.com{link['href']}"
        detail_response = requests.get(detail_url, headers=headers, timeout=10)
        detail_soup = BeautifulSoup(detail_response.text, "html.parser")
        rating = detail_soup.select_one("span[data-test='score-box-OverallScore']")

        if rating:
            return f"⭐ {rating.text.strip()}/5"
    except Exception as e:
        print(f"[Kununu Fehler] {e}")
    return None

async def search_and_send_jobs():
    await bot.wait_until_ready()
    channel = bot.fetch_channel(CHANNEL_ID)
    config = load_config()
    seen = load_seen()
    new_seen = set(seen)

    for kw in config["keywords"]:
        url = f"https://api.adzuna.com/v1/api/jobs/{COUNTRY}/search/1"
        params = {
            "app_id": ADZUNA_APP_ID,
            "app_key": ADZUNA_APP_KEY,
            "results_per_page": 10,
            "what": kw,
            "where": config["location"],
            "distance": config["radius"],
            "max_days_old": 1
        }

        try:
            r = requests.get(url, params=params, timeout=10)
            data = r.json()
            for job in data.get("results", []):
                job_id = job.get("id")
                if job_id in new_seen:
                    continue

                embed = discord.Embed(
                    title=job.get("title", "Ohne Titel"),
                    url=job.get("redirect_url", ""),
                    color=discord.colors.magenta,
                )

                embed.add_field(name="Firma", value=job.get("company", {}).get("display_name", "Unbekannt"), inline=True)
                embed.add_field(name="Ort", value=job.get("location", {}).get("display_name", "Unbekannt"), inline=True)
                rating = fetch_kununu_rating(job.get("company", ""))
                if rating:
                    embed.add_field(name="Kununu", value=rating, inline=True)

                await channel.send(embed=embed)
                new_seen.add(job_id)
                await asyncio.sleep(3)  # Kleine Pause zwischen Jobs

        except Exception as e:
            print(f"[Fehler] {e}")

    save_seen(new_seen)

async def job_loop():
    while True:
        await search_and_send_jobs()
        await asyncio.sleep(1800)  # Alle 10 Minuten
@tree.command(name="config", description="Konfiguriere die Jobsuche")
@app_commands.describe(
    location="Ort der Jobsuche",
    radius="Suchradius in km",
    keywords="Kommagetrennte Keywords (z. B. python, devops)"
)
async def config(interaction: discord.Interaction, location: str, radius: int, keywords: str):
    config = load_config()
    config["location"] = location
    config["radius"] = radius
    config["keywords"] = [k.strip() for k in keywords.split(",")]
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)

    await interaction.response.send_message(
        f"✅ Konfiguration aktualisiert:\n"
        f"📍 Ort: `{location}`\n"
        f"📏 Radius: `{radius} km`\n"
        f"🔎 Keywords: `{', '.join(config['keywords'])}`",
        ephemeral=True
    )


@tree.command(name="show_config", description="Zeigt die aktuelle Konfiguration")
async def show_config(interaction: discord.Interaction):
    config = load_config()
    await interaction.response.send_message(
        f"📍 Ort: `{config['location']}`\n"
        f"📏 Radius: `{config['radius']} km`\n"
        f"🔎 Keywords: `{', '.join(config['keywords'])}`",
        ephemeral=True
    )

@bot.event
async def on_ready():
    print(f"✅ Eingeloggt als {bot.user}")
    await tree.sync()
    bot.loop.create_task(job_loop())

bot.run(TOKEN)
