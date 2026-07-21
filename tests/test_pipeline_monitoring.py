from unittest.mock import Mock

import pytest
from sqlalchemy import create_engine

from database.repository import DataRepository
from etl.pipeline_service import Pipeline


def test_pipeline_records_failed_run() -> None:
    pipeline = Pipeline()

    engine = create_engine(
        "sqlite:///:memory:",
        future=True,
    )

    pipeline.repository = DataRepository(
        engine
    )

    pipeline.extract_hr = Mock(
        side_effect=ValueError(
            "Erreur simulée pour le monitoring"
        )
    )

    with pytest.raises(
        ValueError,
        match="Erreur simulée pour le monitoring",
    ):
        pipeline.run()

    runs = pipeline.repository.read_table(
        pipeline.repository.PIPELINE_RUNS_TABLE
    )

    assert len(runs) == 1

    failed_run = runs.iloc[0]

    assert failed_run["status"] == "FAILED"
    assert failed_run["finished_at"] is not None
    assert failed_run["duration_seconds"] >= 0
    assert (
        failed_run["employee_count"]
        == 0
    )
    assert (
        failed_run["activity_count"]
        == 0
    )
    assert "ValueError" in failed_run[
        "error_message"
    ]
    assert (
        "Erreur simulée pour le monitoring"
        in failed_run["error_message"]
    )