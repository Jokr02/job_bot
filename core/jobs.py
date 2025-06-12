
import requests
import os
from core.config_utils import load_config
from core.logging import logger

APP_ID = os.getenv("ADZUNA_APP_ID")
APP_KEY = os.getenv("ADZUNA_APP_KEY")
COUNTRY = os.getenv("ADZUNA_COUNTRY", "de")

async def search_jobs(days: int = 1):
    config = load_config()
    keywords = config["keywords"]
    jobs = []

    for kw in keywords:
        url = f"https://api.adzuna.com/v1/api/jobs/{COUNTRY}/search/1"
        params = {
            "app_id": APP_ID,
            "app_key": APP_KEY,
            "what": kw,
            "where": config["location"],
            "distance": config["radius"],
            "max_days_old": days,
            "results_per_page": 3,
        }
        try:
            r = requests.get(url, params=params, timeout=10)
            data = r.json()
            jobs += data.get("results", [])
        except Exception as e:
            logger.warning(f"Fehler bei Adzuna-Suche: {e}")

    logger.info(f"🔍 Gefundene Jobs: {len(jobs)}")
    return jobs

def start_job_loop(bot):
    async def job_loop():
        import asyncio
        await bot.wait_until_ready()
        while not bot.is_closed():
            try:
                await search_jobs()
            except Exception as e:
                logger.error(f"Fehler im Job-Loop: {e}")
            await asyncio.sleep(3600)
    bot.loop.create_task(job_loop())
