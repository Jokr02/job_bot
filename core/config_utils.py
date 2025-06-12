
import json
import os

CONFIG_FILE = "config.json"
SAVED_JOBS_FILE = "saved_jobs.json"

def load_config():
    if not os.path.exists(CONFIG_FILE):
        default = {"location": "Coburg", "radius": 100, "keywords": ["admin"], "work_type": "all", "execution_time": "12:00"}
        with open(CONFIG_FILE, "w") as f:
            json.dump(default, f, indent=2)
    with open(CONFIG_FILE) as f:
        return json.load(f)

def load_saved_jobs():
    if os.path.exists(SAVED_JOBS_FILE):
        with open(SAVED_JOBS_FILE) as f:
            return json.load(f)
    return []

def save_job(job):
    jobs = load_saved_jobs()
    jobs.append(job)
    with open(SAVED_JOBS_FILE, "w") as f:
        json.dump(jobs, f, indent=2)
