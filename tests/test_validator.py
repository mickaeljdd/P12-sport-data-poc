import pandas as pd
import pytest

from etl.validator import validate, validate_activities


def build_employees() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "ID salarié": [1],
            "Salaire brut": [40_000.0],
            "Adresse du domicile": ["10 rue Exemple, Montpellier"],
            "Moyen de déplacement": ["Marche"],
        }
    )


def build_activities() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "ID": [1],
            "ID salarié": [1],
            "Date de début de l'activité": ["2026-07-01 08:00:00"],
            "Type": ["Course à pied"],
            "Distance (m)": [5_000],
            "Date de fin de l'activité": ["2026-07-01 08:30:00"],
            "Commentaire": ["Bonne sortie"],
        }
    )


def test_valid_employees_are_accepted():
    result = validate(build_employees())

    pd.testing.assert_frame_equal(result, build_employees())


def test_duplicate_employee_identifier_is_rejected():
    employees = pd.concat(
        [build_employees(), build_employees()],
        ignore_index=True,
    )

    with pytest.raises(ValueError, match="identifiants salariés sont dupliqués"):
        validate(employees)


def test_unknown_transport_is_rejected():
    employees = build_employees()
    employees.loc[0, "Moyen de déplacement"] = "Téléportation"

    with pytest.raises(ValueError, match="moyens de déplacement non reconnus"):
        validate(employees)


def test_activity_with_negative_distance_is_rejected():
    activities = build_activities()
    activities.loc[0, "Distance (m)"] = -1

    with pytest.raises(ValueError, match="distances d'activité sont invalides"):
        validate_activities(activities, build_employees())


def test_activity_with_invalid_dates_is_rejected():
    activities = build_activities()
    activities.loc[0, "Date de fin de l'activité"] = "2026-07-01 07:30:00"

    with pytest.raises(ValueError, match="date de fin antérieure"):
        validate_activities(activities, build_employees())


def test_activity_for_unknown_employee_is_rejected():
    activities = build_activities()
    activities.loc[0, "ID salarié"] = 999

    with pytest.raises(ValueError, match="salariés inconnus"):
        validate_activities(activities, build_employees())
