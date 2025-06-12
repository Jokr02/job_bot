import os
import json
import asyncio
import logging
from datetime import datetime
from core.storage import load_seen_jobs, save_seen_jobs, save_job
from core.discord_utils import send_job_to_discord
from .config import load_config

logger = logging.getLogger(__name__)

SEEN_FILE = "data/jobs_seen.json"

async def job_loop():
    while True:
        try:
            await search_jobs()
        except Exception as e:
            logger.error(f"Fehler im Jobloop: {e}")
        await asyncio.sleep(3600)  # 1h

async def search_jobs():
    config = load_config()
    keywords = config["keywords"]
    seen_ids = load_seen_jobs()
    new_jobs = []

    for kw in keywords:
        job = {
            "id": f"{kw}-{datetime.utcnow().timestamp()}",
            "title": f"Dummy-Job: {kw}",
            "company": "Musterfirma",
            "location": config["location"],
            "url": "https://example.com/job"
        }
        if job["id"] not in seen_ids:
            new_jobs.append(job)
            seen_ids.add(job["id"])

    if new_jobs:
        for job in new_jobs:
            await send_job_to_discord(job)
        save_seen_jobs(seen_ids)

def start_job_loop(bot):
    bot.loop.create_task(job_loop())
