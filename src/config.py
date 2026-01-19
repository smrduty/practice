import os
from dotenv import load_dotenv
from dataclasses import dataclass
from pathlib import Path
import sys
import logging

logger = logging.getLogger(__name__)
load_dotenv()

class ConfigError(Exception):
    """Fatal configuration error"""

def _str_to_bool(value: str) -> bool:
    return value.lower() in ("1", "true", "yes", "on")

def load_config():
    errors = []

    # ====== STRICT MODE =======
    strict_raw = os.getenv("STRICT_CONFIG", "false")
    STRICT_CONFIG = _str_to_bool(strict_raw)

    # ====== BASE DIR ======
    BASE_DIR = Path(__file__).resolve().parents[1]

    # ====== DB PATH ======
    DB_PATH = BASE_DIR / "vacancies.db"

    # ===== REQUIRED ======
    BASE_URL_HHRU = os.getenv("BASE_URL_HHRU")
    if not BASE_URL_HHRU:
        errors.append("BASE_URL_HHRU is required but was not set")

    SEARCH_QUERY = os.getenv("SEARCH_QUERY")
    if not SEARCH_QUERY:
        errors.append("SEARCH_QUERY is required but was not set")

    # ===== OPTIONAL ======
    REGION = os.getenv("REGION")

    # ====== NUMBERIC ====== 
    SALARY_FROM = os.getenv("SALARY_FROM", "0")

    MAX_PAGES = int(os.getenv("MAX_PAGES", "1"))

    SCROLL_TIMES = int(os.getenv("SCROLL_TIMES", "8"))
    
    SCROLL_PAUSE = int(os.getenv("SCROLL_PAUSE", "1000"))

    TIMEOUT = int(os.getenv("TIMEOUT", "10000"))

    # ====== BOOL =======
    HEADLESS = _str_to_bool(os.getenv("HEADLESS", "false"))

    # ====== LOGS DIR ======
    logs_raw = os.getenv("LOGS_DIR")
    if not logs_raw:
        LOGS_DIR = BASE_DIR / "logs"
        logger.warning("LOGS_DIR not set, using default: %s", LOGS_DIR)
    else: 
        LOGS_DIR = Path(logs_raw)

    try:
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        errors.append(f"LOGS_DIR is invalid: {LOGS_DIR} ({e})")

    # ====== RESULTS PATH ======
    result_raw = os.getenv("RESULTS_PATH")
    if not result_raw:
        RESULTS_PATH = BASE_DIR / "results" / "vacancies.csv"
        logger.warning("RESULTS_PATH not set, using default: %s", RESULTS_PATH)
    else: 
        RESULTS_PATH = Path(result_raw)

    try:
        RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        errors.append(f"RESULTS_PATH directory invalid: {RESULTS_PATH.parent}")

    # ===== ERROR HANDLING =====
    if errors:
        for err in errors:
            logger.error(err)
        
        if STRICT_CONFIG:
            raise ConfigError("Invalid configuration")
        
    # ===== TELEGRAM BOT ======
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

    TELEGRAM_ENABLED = bool(
        TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID
    )
    
    return {
        "BASE_DIR": BASE_DIR,
        "BASE_URL_HHRU": BASE_URL_HHRU,
        "SEARCH_QUERY": SEARCH_QUERY,
        "REGION": REGION,
        "SALARY_FROM": SALARY_FROM,
        "HEADLESS": HEADLESS,
        "MAX_PAGES": MAX_PAGES,
        "SCROLL_TIMES": SCROLL_TIMES,
        "SCROLL_PAUSE": SCROLL_PAUSE,
        "TIMEOUT": TIMEOUT,
        "LOGS_DIR": LOGS_DIR,
        "RESULTS_PATH": RESULTS_PATH,
        "STRICT_CONFIG": STRICT_CONFIG,
        "TELEGRAM_ENABLED": TELEGRAM_ENABLED,
        "TELEGRAM_BOT_TOKEN": TELEGRAM_BOT_TOKEN,
        "TELEGRAM_CHAT_ID": TELEGRAM_CHAT_ID,
        "DB_PATH": DB_PATH,
    }
     
config = load_config()



