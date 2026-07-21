import pandas as pd
import pytest
from sqlalchemy import create_engine

from database.repository import DataRepository


@pytest.fixture
def repository() -> DataRepository:
    engine = create_engine(
        "sqlite:///:memory:",
        future=True,
    )

    return DataRepository(engine)


def build_employees() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "ID salarié": [1, 2],
            "Nom": ["Martin", "Durand"],
        }
    )


def build_activities() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "ID": [1, 2],
            "ID salarié": [1, 2],
            "Date de début de l'activité": (
                pd.to_datetime(
                    [
                        "2025-01-01 08:00:00",
                        "2025-01-02 18:00:00",
                    ]
                )
            ),
            "Type": [
                "Runing",
                "Tennis",
            ],
            "Distance (m)": [
                5000,
                None,
            ],
            "Date de fin de l'activité": (
                pd.to_datetime(
                    [
                        "2025-01-01 08:30:00",
                        "2025-01-02 19:00:00",
                    ]
                )
            ),
            "Commentaire": [
                "Bonne sortie",
                "",
            ],
        }
    )


def test_save_and_read_employees(
    repository: DataRepository,
):
    employees = build_employees()

    inserted_count = (
        repository.save_employees(
            employees
        )
    )

    result = repository.read_table(
        "employees"
    )

    assert inserted_count == 2
    assert len(result) == 2
    assert set(result["ID salarié"]) == {1, 2}


def test_save_and_read_activities(
    repository: DataRepository,
):
    activities = build_activities()

    inserted_count = (
        repository.save_activities(
            activities
        )
    )

    result = repository.read_table(
        "activities"
    )

    assert inserted_count == 2
    assert len(result) == 2
    assert set(result["Type"]) == {
        "Runing",
        "Tennis",
    }


def test_null_distance_is_preserved(
    repository: DataRepository,
):
    repository.save_activities(
        build_activities()
    )

    result = repository.read_table(
        "activities"
    )

    tennis = result.loc[
        result["Type"] == "Tennis"
    ].iloc[0]

    assert pd.isna(
        tennis["Distance (m)"]
    )


def test_missing_activity_column_raises_error(
    repository: DataRepository,
):
    activities = (
        build_activities()
        .drop(columns=["Type"])
    )

    with pytest.raises(
        ValueError,
        match="Colonnes manquantes",
    ):
        repository.save_activities(
            activities
        )


def test_unknown_table_is_rejected(
    repository: DataRepository,
):
    with pytest.raises(
        ValueError,
        match="Table non autorisée",
    ):
        repository.read_table(
            "unknown_table"
        )


def test_original_dataframe_is_not_modified(
    repository: DataRepository,
):
    employees = build_employees()
    original = employees.copy(
        deep=True
    )

    repository.save_employees(
        employees
    )

    pd.testing.assert_frame_equal(
        employees,
        original,
    )

def build_pipeline_run() -> pd.DataFrame:
    return pd.DataFrame(
    [
        {
            "run_id": "run-test-001",
            "started_at": pd.Timestamp(
                "2026-07-19 10:00:00"
            ),
            "finished_at": pd.Timestamp(
                "2026-07-19 10:00:05"
            ),
            "duration_seconds": 5.0,
            "status": "SUCCESS",
            "employee_count": 161,
            "activity_count": 9110,
            "slack_message_count": 9110,
            "bonus_total": 37809.50,
            "wellbeing_days": 475,
            "error_message": None,
        }
    ]
)

def test_save_and_read_pipeline_run(
repository: DataRepository,
):
    run = build_pipeline_run()

    inserted_count = (
        repository.save_pipeline_run(run)
    )

    result = repository.read_table(
        "pipeline_runs"
    )

    assert inserted_count == 1
    assert len(result) == 1
    assert result.iloc[0]["status"] == "SUCCESS"

def test_pipeline_runs_are_appended(
repository: DataRepository,
):
    repository.save_pipeline_run(
        build_pipeline_run()
    )

    second_run = build_pipeline_run()
    second_run["run_id"] = "run-test-002"

    repository.save_pipeline_run(
        second_run
    )

    result = repository.read_table(
        "pipeline_runs"
    )

    assert len(result) == 2