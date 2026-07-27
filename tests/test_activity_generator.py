from datetime import date

import pandas as pd
import pytest

from simulation.activity_generator import (
    ActivityGenerator,
)


START_DATE = date(2025, 1, 1)
END_DATE = date(2025, 3, 31)


def build_employees() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "ID salarié": [1, 2, 3],
            "Pratique d'un sport": [
                "Tennis",
                None,
                "Runing",
            ],
        }
    )


def generate_test_activities() -> pd.DataFrame:
    generator = ActivityGenerator(seed=42)

    return generator.generate(
        build_employees(),
        start_date=START_DATE,
        end_date=END_DATE,
    )


def test_generates_only_for_sporting_employees():
    result = generate_test_activities()

    assert not result.empty

    assert set(
        result["ID salarié"].unique()
    ) == {1, 3}


def test_expected_columns():
    result = generate_test_activities()

    assert list(result.columns) == (
        ActivityGenerator.ACTIVITY_COLUMNS
    )


def test_activity_ids_are_unique_and_sequential():
    result = generate_test_activities()

    assert result["ID"].is_unique

    assert result["ID"].tolist() == list(
        range(1, len(result) + 1)
    )


def test_declared_sport_is_preserved():
    result = generate_test_activities()

    tennis = result.loc[
        result["ID salarié"] == 1,
        "Type",
    ]

    running = result.loc[
        result["ID salarié"] == 3,
        "Type",
    ]

    assert set(tennis) == {"Tennis"}
    assert set(running) == {"Runing"}


def test_running_generates_distance():
    result = generate_test_activities()

    running = result.loc[
        result["Type"] == "Runing"
    ]

    assert not running.empty
    assert running["Distance (m)"].notna().all()
    assert (running["Distance (m)"] > 0).all()


def test_tennis_has_no_distance():
    result = generate_test_activities()

    tennis = result.loc[
        result["Type"] == "Tennis"
    ]

    assert not tennis.empty
    assert tennis["Distance (m)"].isna().all()


def test_end_date_is_after_start_date():
    result = generate_test_activities()

    assert (
        result["Date de fin de l'activité"]
        >
        result["Date de début de l'activité"]
    ).all()


def test_activity_dates_are_inside_requested_period():
    result = generate_test_activities()

    activity_dates = (
        result["Date de début de l'activité"]
        .dt.date
    )

    assert (
        activity_dates >= START_DATE
    ).all()

    assert (
        activity_dates <= END_DATE
    ).all()


def test_generation_is_reproducible():
    first = ActivityGenerator(seed=42).generate(
        build_employees(),
        start_date=START_DATE,
        end_date=END_DATE,
    )

    second = ActivityGenerator(seed=42).generate(
        build_employees(),
        start_date=START_DATE,
        end_date=END_DATE,
    )

    pd.testing.assert_frame_equal(
        first,
        second,
    )


def test_empty_sports_produce_empty_dataframe():
    employees = pd.DataFrame(
        {
            "ID salarié": [1, 2],
            "Pratique d'un sport": [
                None,
                "",
            ],
        }
    )

    result = ActivityGenerator(
        seed=42
    ).generate(
        employees,
        start_date=START_DATE,
        end_date=END_DATE,
    )

    assert result.empty

    assert list(result.columns) == (
        ActivityGenerator.ACTIVITY_COLUMNS
    )


def test_missing_column_raises_error():
    employees = pd.DataFrame(
        {
            "ID salarié": [1]
        }
    )

    with pytest.raises(
        ValueError,
        match="Colonnes manquantes",
    ):
        ActivityGenerator().generate(
            employees,
            start_date=START_DATE,
            end_date=END_DATE,
        )


def test_invalid_period_raises_error():
    with pytest.raises(
        ValueError,
        match="date de début",
    ):
        ActivityGenerator().generate(
            build_employees(),
            start_date=date(2025, 4, 1),
            end_date=date(2025, 3, 1),
        )

def test_aucune_is_not_recognized_as_sport():
    employee = pd.Series(
        {
            "Pratique d'un sport": "Aucune"
        }
    )

    assert (
        ActivityGenerator._practices_sport(
            employee
        )
        is False
    )

def test_employees_without_sport_produce_empty_dataframe():
    employees = pd.DataFrame(
        {
            "ID salarié": [1, 2, 3],
            "Pratique d'un sport": [
                None,
                "",
                "Aucune",
            ],
        }
    )

    result = ActivityGenerator(
        seed=42
    ).generate(
        employees,
        start_date=START_DATE,
        end_date=END_DATE,
    )

    assert result.empty

def test_live_generator_creates_requested_incremental_ids():
    from simulation.live_activity_generator import LiveActivityGenerator

    result = LiveActivityGenerator(seed=42).generate(
        build_employees(),
        starting_id=101,
        activity_count=5,
        activity_date=START_DATE,
    )

    assert len(result) == 5
    assert result["ID"].tolist() == [101, 102, 103, 104, 105]
    assert set(result["ID salarié"]).issubset({1, 3})
    assert (
        result["Date de début de l'activité"].dt.date == START_DATE
    ).all()
