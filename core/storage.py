# core/storage.py

import json
import os
from core.logging import logger

SAVED_JOBS_FILE = os.getenv("SAVED_JOBS_FILE", "saved_jobs.json")

def save_job(job):
    try:
        if os.path.exists(SAVED_JOBS_FILE):
            with open(SAVED_JOBS_FILE, "r") as f:
                jobs = json.load(f)
        else:
            jobs = []

        if not any(j.get("id") == job.get("id") for j in jobs):
            jobs.append(job)
            with open(SAVED_JOBS_FILE, "w") as f:
                json.dump(jobs, f, indent=2)
            logger.info(f"💾 Job gespeichert: {job['title']}")
    except Exception as e:
        logger.error(f"Fehler beim Speichern des Jobs: {e}")
