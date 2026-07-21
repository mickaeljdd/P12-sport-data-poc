import pandas as pd

from services.distance_service import DistanceService


def test_compute_adds_distance_column():
    source = pd.DataFrame(
        {
            "Moyen de déplacement": [
                "Marche",
                "Vélo",
                "Voiture",
            ]
        }
    )

    service = DistanceService()

    result = service.compute(source)

    assert "Distance domicile-entreprise (km)" in result.columns
    assert len(result) == 3
    assert result["Distance domicile-entreprise (km)"].notna().all()
    assert (result["Distance domicile-entreprise (km)"] >= 0).all()


def test_compute_does_not_modify_source_dataframe():
    source = pd.DataFrame(
        {
            "Moyen de déplacement": ["Marche"]
        }
    )

    service = DistanceService()

    service.compute(source)

    assert "Distance domicile-entreprise (km)" not in source.columns