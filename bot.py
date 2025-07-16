import discord
import json
import os
import asyncio
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))
ADZUNA_APP_ID = os.getenv("ADZUNA_APP_ID")
ADZUNA_APP_KEY = os.getenv("ADZUNA_APP_KEY")
COUNTRY = os.getenv("ADZUNA_COUNTRY", "de")

CONFIG_FILE = "config.json"
SEEN_FILE = "jobs_seen.json"

intents = discord.Intents.default()
bot = discord.Client(intents=intents)

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

async def search_and_send_jobs():
    await bot.wait_until_ready()
    channel = bot.get_channel(CHANNEL_ID)
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
                if job_id in seen:
                    continue

                embed = discord.Embed(
                    title=job.get("title", "Ohne Titel"),
                    url=job.get("redirect_url", ""),
                    color=0x3498db
                )
                embed.add_field(name="Firma", value=job.get("company", {}).get("display_name", "Unbekannt"), inline=True)
                embed.add_field(name="Ort", value=job.get("location", {}).get("display_name", "Unbekannt"), inline=True)

                await channel.send(embed=embed)
                new_seen.add(job_id)
                await asyncio.sleep(3)  # Kleine Pause zwischen Jobs

        except Exception as e:
            print(f"[Fehler] {e}")

    save_seen(new_seen)

async def job_loop():
    while True:
        await search_and_send_jobs()
        await asyncio.sleep(600)  # Alle 10 Minuten

@bot.event
async def on_ready():
    print(f"✅ Eingeloggt als {bot.user}")
    bot.loop.create_task(job_loop())

bot.run(TOKEN)
