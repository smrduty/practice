import logging
import os
from config import LOGS_DIR


#os.makedirs("logs", exist_ok=True)

#logs_path = r"D:\projects\project1\logs\app.log"

logging.basicConfig(
    #filename=logs_path,
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(LOGS_DIR, encoding="utf-8"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

