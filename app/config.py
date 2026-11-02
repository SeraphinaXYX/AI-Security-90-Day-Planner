"""Application configuration management."""
import os
import json
from pathlib import Path

APP_NAME = "AI Security 90-Day Planner"
APP_VERSION = "1.0.0"
APP_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = APP_DIR / "data"
DB_PATH = DATA_DIR / "planner.db"
CONFIG_PATH = DATA_DIR / "config.json"
BACKUP_DIR = DATA_DIR / "backups"

DEFAULT_CONFIG = {
    "reminder_morning": "09:00",
    "reminder_evening": "19:00",
    "reminder_night": "22:00",
    "reminders_enabled": True,
    "reminder_morning_enabled": True,
    "reminder_evening_enabled": True,
    "reminder_night_enabled": True,
    "startup_enabled": False,
    "startup_asked": False,
    "theme": "dark",
    "first_launch": True,
}


def ensure_dirs():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)


def load_file_config():
    ensure_dirs()
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            stored = json.load(f)
        merged = {**DEFAULT_CONFIG, **stored}
        return merged
    return dict(DEFAULT_CONFIG)


def save_file_config(cfg: dict):
    ensure_dirs()
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)
