import json
import os
import logging

CONFIG_FILE = "config.json"
logger = logging.getLogger(__name__)

default_config = {
    "location": "Berlin",
    "radius": 25,
    "keywords": ["Python", "DevOps"],
    "search_interval_minutes": 60
}

def load_config():
    if not os.path.exists(CONFIG_FILE):
        logger.warning("⚠️ Keine config.json gefunden. Erstelle Standardkonfiguration.")
        save_config(default_config)
        return default_config

    try:
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
            return validate_config(config)
    except Exception as e:
        logger.error(f"❌ Fehler beim Laden der Konfiguration: {e}")
        return default_config

def save_config(config):
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        logger.error(f"❌ Fehler beim Speichern der Konfiguration: {e}")

def validate_config(config):
    validated = default_config.copy()
    validated.update(config)
    return validated
