from pathlib import Path
from unittest.mock import Mock

import pandas as pd

from services.distance_cache import (
    DistanceCache,
)
from services.google_maps_distance_service import (
    GoogleMapsDistanceService,
)


def test_second_execution_uses_persistent_cache(
    tmp_path: Path,
):
    cache = DistanceCache(
        tmp_path / "cache.csv"
    )

    service = GoogleMapsDistanceService(
        api_key="fake-key",
        company_address=(
            "1362 avenue des Platanes, "
            "34970 Lattes"
        ),
        cache=cache,
    )

    response = Mock()
    response.status_code = 200
    response.raise_for_status.return_value = None
    response.json.return_value = {
        "routes": [
            {
                "distanceMeters": 26700,
            }
        ]
    }

    service.session.post = Mock(
        return_value=response
    )

    employees = pd.DataFrame(
        {
            service.ADDRESS_COLUMN: [
                "10 rue Exemple, Montpellier",
            ],
            service.TRANSPORT_COLUMN: ["Marche"],
        }
    )

    first_result = service.compute(
        employees
    )

    second_result = service.compute(
        employees
    )

    assert (
        first_result.loc[
            0,
            "Distance domicile-entreprise (km)",
        ]
        == 26.7
    )

    assert (
        second_result.loc[
            0,
            "Distance domicile-entreprise (km)",
        ]
        == 26.7
    )

    service.session.post.assert_called_once()


def test_uses_the_google_travel_mode_matching_transport(
    tmp_path: Path,
):
    cache = DistanceCache(tmp_path / "cache.csv")
    service = GoogleMapsDistanceService(
        api_key="fake-key",
        cache=cache,
    )

    response = Mock()
    response.status_code = 200
    response.raise_for_status.return_value = None
    response.json.return_value = {
        "routes": [{"distanceMeters": 1_000}]
    }
    service.session.post = Mock(return_value=response)

    employees = pd.DataFrame(
        {
            service.ADDRESS_COLUMN: [
                "1 rue A, Montpellier",
                "2 rue B, Montpellier",
                "3 rue C, Montpellier",
                "4 rue D, Montpellier",
            ],
            service.TRANSPORT_COLUMN: [
                "Marche",
                "Vélo/Trottinette/Autres",
                "Transports en commun",
                "Véhicule thermique/électrique",
            ],
        }
    )

    service.compute(employees)

    travel_modes = [
        call.kwargs["json"]["travelMode"]
        for call in service.session.post.call_args_list
    ]

    assert travel_modes == [
        "WALK",
        "BICYCLE",
        "TRANSIT",
        "DRIVE",
    ]


def test_cache_keeps_distances_separate_for_each_travel_mode(
    tmp_path: Path,
):
    cache = DistanceCache(tmp_path / "cache.csv")
    cache.set("10 rue Exemple, Montpellier", 3.0, "WALK")
    cache.set("10 rue Exemple, Montpellier", 5.0, "BICYCLE")

    assert cache.get("10 rue Exemple, Montpellier", "WALK") == 3.0
    assert cache.get("10 rue Exemple, Montpellier", "BICYCLE") == 5.0
