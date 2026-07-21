import requests
import random
import pandas as pd
from config import GOOGLE_MAPS_API_KEY
from config import COMPANY_ADDRESS


class GoogleDistanceService:

    URL = "https://maps.googleapis.com/maps/api/distancematrix/json"

    def get_distance(self, origin):

        params = {
            "origins": origin,
            "destinations": COMPANY_ADDRESS,
            "key": GOOGLE_MAPS_API_KEY,
            "units": "metric"
        }

        response = requests.get(
            self.URL,
            params=params,
            timeout=30
        )

        response.raise_for_status()

        data = response.json()

        return data
    
class DistanceService:

    DISTANCE_COLUMN = "Distance domicile-entreprise (km)"

    def __init__(self):
        random.seed(42)      # Toujours les mêmes résultats

    def generate_distance(self, transport: str) -> float:

        transport = str(transport).strip()

        if transport == "Marche":
            return round(random.uniform(0.5, 25), 1)

        elif transport in {
            "Vélo",
            "Trottinette",
            "Vélo/Trottinette/Autres",
        }:
            return round(random.uniform(2, 35), 1)

        elif transport in {
            "Voiture",
            "Véhicule thermique/électrique",
        }:
            return round(random.uniform(5, 60), 1)

        elif transport in {
            "Transport en commun",
            "Transports en commun",
        }:
            return round(random.uniform(5, 40), 1)

        return round(random.uniform(1, 30), 1)

    def compute(self, df: pd.DataFrame):

        df = df.copy()

        df[self.DISTANCE_COLUMN] = (
            df["Moyen de déplacement"]
            .apply(self.generate_distance)
        )

        return df
