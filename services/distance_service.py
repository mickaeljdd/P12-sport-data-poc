import requests

from config import GOOGLE_API_KEY
from config import COMPANY_ADDRESS


class GoogleDistanceService:

    URL = "https://maps.googleapis.com/maps/api/distancematrix/json"

    def get_distance(self, origin):

        params = {
            "origins": origin,
            "destinations": COMPANY_ADDRESS,
            "key": GOOGLE_API_KEY,
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