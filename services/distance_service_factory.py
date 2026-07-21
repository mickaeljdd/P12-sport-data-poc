from config import DISTANCE_PROVIDER
from services.distance_service import (
    DistanceService,
)
from services.google_maps_distance_service import (
    GoogleMapsDistanceService,
)


def create_distance_service():
    if DISTANCE_PROVIDER == "google":
        return GoogleMapsDistanceService()

    if DISTANCE_PROVIDER == "mock":
        return DistanceService()

    raise ValueError(
        "Fournisseur de distance inconnu : "
        f"{DISTANCE_PROVIDER}"
    )