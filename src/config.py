import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("BASE_URL")
SEARCH_QUERY = os.getenv("SEARCH_QUERY")

HEADLESS = os.getenv("HEADLESS", "true").lower() == "true"

MAX_PAGES = int(os.getenv("MAX_PAGES", 1))
SCROLL_TIMES = int(os.getenv("SCROLL_TIMES", 3))
SCROLL_PAUSE = int(os.getenv("SCROLL_PAUSE", 1000))
TIMEOUT = int(os.getenv("TIMEOUT", 10000))

LOGS_DIR = os.getenv("LOGS_DIR")

if not BASE_URL:
    raise ValueError("BASE_URL was not set in .env")

if not SEARCH_QUERY:
    raise ValueError("SEARCH_QUERY was not set in .env")

