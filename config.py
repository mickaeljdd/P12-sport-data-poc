"""
Configuration du projet Sport Data POC
"""

# Adresse entreprise

COMPANY_ADDRESS = "1362 Avenue des Platanes, 34970 Lattes"

# Prime sportive

SPORT_BONUS_RATE = 0.05

# Jours bien-être

WELLBEING_DAYS = 5

# Nombre minimum d'activités

MIN_ACTIVITIES = 15

# Distances maximales (km)

MAX_DISTANCE = {
    "Marche": 15,
    "Vélo": 25,
    "Trottinette": 25,
    "Vélo/Trottinette/Autres": 25,
}

# Modes de déplacement éligibles

ELIGIBLE_TRANSPORT = [
    "Marche",
    "Vélo",
    "Trottinette"
]

from dotenv import load_dotenv
import os

load_dotenv()
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent
DATABASE_DIR = ROOT_DIR / "database"
DATABASE_PATH = DATABASE_DIR / "sport_poc.db"

DATABASE_URL = f"sqlite:///{DATABASE_PATH.as_posix()}"

GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

COMPANY_ADDRESS = "1362 Avenue des Platanes, 34970 Lattes"

DISTANCE_PROVIDER = os.getenv(
    "DISTANCE_PROVIDER",
    "mock",
).strip().lower()

GOOGLE_ROUTES_URL = (
    "https://routes.googleapis.com/"
    "directions/v2:computeRoutes"
)

GOOGLE_MAPS_TIMEOUT_SECONDS = 15

DISTANCE_COLUMN = (
    "Distance domicile-entreprise (km)"
)

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")

SLACK_TIMEOUT_SECONDS = int(
    os.getenv(
        "SLACK_TIMEOUT_SECONDS",
        "10",
    )
)

LIVE_STREAM_MIN_INTERVAL_SECONDS = float(
    os.getenv("LIVE_STREAM_MIN_INTERVAL_SECONDS", "1")
)

LIVE_STREAM_MAX_INTERVAL_SECONDS = float(
    os.getenv("LIVE_STREAM_MAX_INTERVAL_SECONDS", "3")
)

MAX_INCREMENTAL_ACTIVITIES = 10
MIN_INCREMENTAL_ACTIVITIES = 3