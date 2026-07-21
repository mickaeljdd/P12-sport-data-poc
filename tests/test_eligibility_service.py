import pandas as pd

from services.eligibility_service import EligibilityService


def build_test_dataframe() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "ID salarié": [1, 2, 3, 4],
            "Moyen de déplacement": [
                "Marche",
                "Marche",
                "Vélo",
                "Voiture",
            ],
            "Distance domicile-entreprise (km)": [
                10.0,
                18.0,
                20.0,
                5.0,
            ],
            "Salaire brut": [
                40_000.0,
                40_000.0,
                50_000.0,
                60_000.0,
            ],
        }
    )


def test_transport_eligibility():
    service = EligibilityService()

    result = service.compute(build_test_dataframe())

    assert bool(result.loc[0, "transport_eligible"]) is True
    assert bool(result.loc[1, "transport_eligible"]) is False
    assert bool(result.loc[2, "transport_eligible"]) is True
    assert bool(result.loc[3, "transport_eligible"]) is False


def test_bonus_is_five_percent_for_eligible_employee():
    service = EligibilityService()

    result = service.compute(build_test_dataframe())

    assert result.loc[0, "bonus"] == 2_000.0
    assert result.loc[2, "bonus"] == 2_500.0


def test_no_bonus_for_ineligible_employee():
    service = EligibilityService()

    result = service.compute(build_test_dataframe())

    assert result.loc[1, "bonus"] == 0.0
    assert result.loc[3, "bonus"] == 0.0


def test_grouped_bike_scooter_other_transport_uses_25_km_limit():
    source = pd.DataFrame(
        {
            "ID salarié": [1, 2],
            "Moyen de déplacement": [
                "Vélo/Trottinette/Autres",
                "Vélo/Trottinette/Autres",
            ],
            "Distance domicile-entreprise (km)": [
                25.0,
                25.1,
            ],
            "Salaire brut": [
                40_000.0,
                40_000.0,
            ],
        }
    )

    result = EligibilityService().compute(source)

    assert bool(result.loc[0, "transport_eligible"]) is True
    assert result.loc[0, "bonus"] == 2_000.0
    assert bool(result.loc[1, "transport_eligible"]) is False


def test_source_dataframe_is_not_modified():
    source = build_test_dataframe()
    service = EligibilityService()

    service.compute(source)

    assert "transport_eligible" not in source.columns
    assert "bonus" not in source.columns
