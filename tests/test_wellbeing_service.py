import pandas as pd
import pytest

from services.wellbeing_service import (
    WellbeingService,
)


def build_employees() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "ID salarié": [1, 2, 3],
            "Nom": [
                "Martin",
                "Durand",
                "Petit",
            ],
        }
    )


def build_activities() -> pd.DataFrame:
    employee_one = pd.DataFrame(
        {
            "ID salarié": [1] * 15,
        }
    )

    employee_two = pd.DataFrame(
        {
            "ID salarié": [2] * 14,
        }
    )

    return pd.concat(
        [
            employee_one,
            employee_two,
        ],
        ignore_index=True,
    )


def test_employee_with_15_activities_is_eligible():
    service = WellbeingService()

    result = service.compute(
        build_employees(),
        build_activities(),
    )

    employee = result.loc[
        result["ID salarié"] == 1
    ].iloc[0]

    assert employee["Nombre d'activités"] == 15
    assert bool(
        employee["Éligible jours bien-être"]
    ) is True
    assert (
        employee["Jours bien-être accordés"]
        == 5
    )


def test_employee_with_14_activities_is_not_eligible():
    service = WellbeingService()

    result = service.compute(
        build_employees(),
        build_activities(),
    )

    employee = result.loc[
        result["ID salarié"] == 2
    ].iloc[0]

    assert employee["Nombre d'activités"] == 14
    assert bool(
        employee["Éligible jours bien-être"]
    ) is False
    assert (
        employee["Jours bien-être accordés"]
        == 0
    )


def test_employee_without_activity_is_not_eligible():
    service = WellbeingService()

    result = service.compute(
        build_employees(),
        build_activities(),
    )

    employee = result.loc[
        result["ID salarié"] == 3
    ].iloc[0]

    assert employee["Nombre d'activités"] == 0
    assert bool(
        employee["Éligible jours bien-être"]
    ) is False
    assert (
        employee["Jours bien-être accordés"]
        == 0
    )


def test_original_dataframe_is_not_modified():
    employees = build_employees()
    original = employees.copy()

    service = WellbeingService()

    service.compute(
        employees,
        build_activities(),
    )

    pd.testing.assert_frame_equal(
        employees,
        original,
    )


def test_missing_employee_id_column_raises_error():
    employees = pd.DataFrame(
        {
            "Nom": ["Martin"]
        }
    )

    activities = pd.DataFrame(
        {
            "ID salarié": [1]
        }
    )

    service = WellbeingService()

    with pytest.raises(
        ValueError,
        match="DataFrame salariés",
    ):
        service.compute(
            employees,
            activities,
        )


def test_missing_activity_employee_id_column_raises_error():
    employees = pd.DataFrame(
        {
            "ID salarié": [1]
        }
    )

    activities = pd.DataFrame(
        {
            "Type": ["Tennis"]
        }
    )

    service = WellbeingService()

    with pytest.raises(
        ValueError,
        match="DataFrame activités",
    ):
        service.compute(
            employees,
            activities,
        )