import logging
import os
from config import config


#os.makedirs("logs", exist_ok=True)

#logs_path = r"D:\projects\project1\logs\app.log"

def setup_logging():
    handlers = [logging.StreamHandler()]

    if config['LOGS_DIR']:
        try:
            if os.path.isdir(config['LOGS_DIR']):
                os.makedirs(config['LOGS_DIR'], exist_ok=True)
                log_file = os.path.join(config['LOGS_DIR'], "app.log")
            else:
                os.makedirs(os.path.dirname(config['LOGS_DIR']), exist_ok=True)
                log_file = config['LOGS_DIR']

            handlers.insert(
                0,
                logging.FileHandler(log_file, encoding="utf-8")
            )
        except Exception as e:
            print(f"[logging] File logging disabled: {e}")

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        handlers=handlers
    )

setup_logging()
logger = logging.getLogger(__name__)

