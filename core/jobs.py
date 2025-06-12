import os
import json
import re
import requests
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from core.logging import logger

CONFIG_FILE = os.path.join("data", "config.json")
JOBS_SEEN_FILE = os.path.join("data", "jobs_seen.json")
SAVED_JOBS_FILE = os.path.join("data", "saved_jobs.json")

def load_config():
    if not os.path.exists(CONFIG_FILE):
        default = {
            "location": "Berlin",
            "radius": 50,
            "keywords": ["IT Support"],
            "work_type": "all",
            "execution_time": "09:00"
        }
        with open(CONFIG_FILE, "w") as f:
            json.dump(default, f, indent=2)
    with open(CONFIG_FILE) as f:
        return json.load(f)

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
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

def export_saved_jobs():
    jobs = load_saved_jobs()
    lines = ["Titel,Unternehmen,Ort,URL"]
    for job in jobs:
        line = f'"{job["title"]}","{job["company"]}","{job["location"]}","{job["url"]}"'
        lines.append(line)
    return "\n".join(lines)

def highlight_keywords(text, keywords):
    for kw in sorted(keywords, key=len, reverse=True):
        text = re.sub(rf"(?i)\b({re.escape(kw)})\b", r"**\1**", text)
    return text
