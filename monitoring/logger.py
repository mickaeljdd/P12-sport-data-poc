import logging
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

LOG_FOLDER = ROOT / "logs"

LOG_FOLDER.mkdir(exist_ok=True)

LOG_FILE = LOG_FOLDER / "pipeline.log"


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("sport-data")