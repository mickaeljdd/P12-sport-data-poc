import pandas as pd

from config import (
    MAX_INCREMENTAL_ACTIVITIES,
    MIN_INCREMENTAL_ACTIVITIES,
)
from simulation.live_activity_generator import LiveActivityGenerator


def make_employees() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "ID salarié": 1,
                "Pratique d'un sport": "Running",
            },
            {
                "ID salarié": 2,
                "Pratique d'un sport": "Cyclisme",
            },
            {
                "ID salarié": 3,
                "Pratique d'un sport": "",
            },
        ]
    )


def test_generate_returns_dataframe():
    generator = LiveActivityGenerator(seed=42)

    activities = generator.generate(
        employees=make_employees(),
        starting_id=1,
        activity_count=5
    )

    assert isinstance(activities, pd.DataFrame)


def test_generate_returns_requested_activity_count() -> None:
    generator = LiveActivityGenerator(seed=42)

    activities = generator.generate(
        employees=make_employees(),
        starting_id=1,
        activity_count=5,
    )

    assert len(activities) == 5


def test_generate_ids_are_sequential():
    generator = LiveActivityGenerator(seed=42)

    activities = generator.generate(
        employees=make_employees(),
        starting_id=10,
        activity_count=5,
    )

    expected_ids = list(
        range(
            10,
            10 + len(activities),
        )
    )

    assert activities["ID"].tolist() == expected_ids


def test_generate_only_sporting_employees():
    generator = LiveActivityGenerator(seed=42)

    activities = generator.generate(
        employees=make_employees(),
        starting_id=1,
        activity_count=5
    )

    assert set(activities["ID salarié"]).issubset({1, 2})