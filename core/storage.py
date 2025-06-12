import json
import os

SEEN_FILE = "data/jobs_seen.json"
SAVED_FILE = "data/saved_jobs.json"

def load_seen_jobs():
    if not os.path.exists(SEEN_FILE):
        return set()
    with open(SEEN_FILE) as f:
        return set(json.load(f).get("posted_ids", []))

def save_seen_jobs(ids):
    with open(SEEN_FILE, "w") as f:
        json.dump({"posted_ids": list(ids)}, f, indent=2)

def save_job(job):
    jobs = []
    if os.path.exists(SAVED_FILE):
        with open(SAVED_FILE) as f:
            jobs = json.load(f)
    jobs.append(job)
    with open(SAVED_FILE, "w") as f:
        json.dump(jobs, f, indent=2)

def load_saved_jobs():
    if not os.path.exists(SAVED_FILE):
        return []
    with open(SAVED_FILE) as f:
        return json.load(f)

def clear_saved_jobs():
    with open(SAVED_FILE, "w") as f:
        json.dump([], f)
