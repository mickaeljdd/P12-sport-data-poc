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
    "Trottinette": 25
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

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

COMPANY_ADDRESS = "1362 Avenue des Platanes, 34970 Lattes"

DISTANCE_PROVIDER = "google"