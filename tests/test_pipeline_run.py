from monitoring.pipeline_run import PipelineRun


def test_pipeline_run_starts_with_running_status() -> None:
    pipeline_run = PipelineRun.start()

    assert pipeline_run.run_id
    assert pipeline_run.started_at is not None
    assert pipeline_run.finished_at is None
    assert pipeline_run.status == "RUNNING"
    assert pipeline_run.employee_count == 0
    assert pipeline_run.activity_count == 0
    assert pipeline_run.error_message is None
    
def test_pipeline_run_converts_to_dataframe() -> None:
    pipeline_run = PipelineRun.start()

    result = pipeline_run.to_dataframe()

    assert len(result) == 1
    assert result.iloc[0]["run_id"] == pipeline_run.run_id
    assert result.iloc[0]["status"] == "RUNNING"