import pandas as pd

from etl.transform import normalize_transport


def test_normalizes_vehicle_transport_label_from_hr_file():
    source = pd.DataFrame(
        {
            "Moyen de déplacement": [
                "véhicule thermique/électrique",
            ]
        }
    )

    result = normalize_transport(source)

    assert result.loc[0, "Moyen de déplacement"] == (
        "Véhicule thermique/électrique"
    )
