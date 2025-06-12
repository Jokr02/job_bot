import os
import json
import requests
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import asyncio
from core.logging import logger
from core.config_utils import load_config
from core.discord_utils import send_job_to_discord

DATA_DIR = "data"
SEEN_FILE = os.path.join(DATA_DIR, "jobs_seen.json")
SAVED_FILE = os.path.join(DATA_DIR, "saved_jobs.json")

# -------------------- Datenspeicherung --------------------

def load_seen_jobs():
    if not os.path.exists(SEEN_FILE):
        return set()
    with open(SEEN_FILE, "r") as f:
        return set(json.load(f).get("posted_ids", []))

def save_seen_jobs(job_ids):
    with open(SEEN_FILE, "w") as f:
        json.dump({"posted_ids": list(job_ids)}, f, indent=2)

def save_job(job):
    jobs = load_saved_jobs()
    jobs.append(job)
    with open(SAVED_FILE, "w") as f:
        json.dump(jobs, f, indent=2)

def load_saved_jobs():
    if os.path.exists(SAVED_FILE):
        with open(SAVED_FILE) as f:
            return json.load(f)
    return []

def clear_saved_jobs():
    with open(SAVED_FILE, "w") as f:
        json.dump([], f)

def export_saved_jobs():
    jobs = load_saved_jobs()
    lines = ["Titel,Unternehmen,Ort,URL"]
    for job in jobs:
        line = f'"{job["title"]}","{job["company"]}","{job["location"]}","{job["url"]}"'
        lines.append(line)
    return "\n".join(lines)

# -------------------- Jobquellen --------------------

def fetch_jobs_adzuna(keywords, location, radius, days=1):
    app_id = os.getenv("ADZUNA_APP_ID")
    app_key = os.getenv("ADZUNA_APP_KEY")
    country = os.getenv("ADZUNA_COUNTRY", "de")
    jobs = []
    for kw in keywords:
        url = f"https://api.adzuna.com/v1/api/jobs/{country}/search/1"
        params = {
            "app_id": app_id,
            "app_key": app_key,
            "what": kw,
            "where": location,
            "distance": radius,
            "results_per_page": 5,
            "sort_by": "date",
            "max_days_old": days
        }
        try:
            r = requests.get(url, params=params, timeout=10)
            r.raise_for_status()
            for job in r.json().get("results", []):
                jobs.append({
                    "id": job["id"],
                    "title": job["title"],
                    "company": job.get("company", {}).get("display_name"),
                    "location": job.get("location", {}).get("display_name"),
                    "url": job["redirect_url"]
                })
        except Exception as e:
            logger.warning(f"Adzuna Fehler: {e}")
    return jobs

def fetch_jobs_arbeitsagentur(keywords, location, radius, days=1):
    jobs = []
    for kw in keywords:
        try:
            url = f"https://jobboerse.arbeitsagentur.de/vamJB/startseite.html?aa=1&suchbegriff={kw}&ort={location}&umkreis={radius}"
            r = requests.get(url, timeout=10)
            soup = BeautifulSoup(r.text, "html.parser")
            for result in soup.select("div.result"):
                jobs.append({
                    "id": result.get("id"),
                    "title": result.find("h2").text.strip(),
                    "company": "Arbeitsagentur",
                    "location": location,
                    "url": url
                })
        except Exception as e:
            logger.warning(f"Arbeitsagentur Fehler: {e}")
    return jobs

# -------------------- Zentrale Suche --------------------

async def search_jobs(days=1):
    config = load_config()
    keywords = config.get("keywords", [])
    location = config.get("location", "Berlin")
    radius = config.get("radius", 30)

    seen_ids = load_seen_jobs()
    new_jobs = []

    all_jobs = []
    all_jobs.extend(fetch_jobs_adzuna(keywords, location, radius, days))
    all_jobs.extend(fetch_jobs_arbeitsagentur(keywords, location, radius, days))

    for job in all_jobs:
        if job["id"] not in seen_ids:
            seen_ids.add(job["id"])
            new_jobs.append(job)

    save_seen_jobs(seen_ids)

    if new_jobs:
        logger.info(f"🔍 Gefundene Jobs: {len(new_jobs)}")
        for job in new_jobs:
            await send_job_to_discord(job)
    else:
        logger.info("ℹ️ Keine neuen Jobs gefunden.")

# -------------------- Automatische Wiederholung --------------------

def start_job_loop(bot):
    async def job_loop():
        await bot.wait_until_ready()
        while not bot.is_closed():
            try:
                await search_jobs()
            except Exception as e:
                logger.exception("Fehler im Jobloop")
            await asyncio.sleep(3600)  # alle 60 Minuten

    bot.loop.create_task(job_loop())
