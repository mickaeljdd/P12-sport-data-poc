from unittest.mock import Mock, patch

import pandas as pd

from etl.pipeline_service import Pipeline


def create_employees() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "ID salarié": [1, 2],
            "bonus": [100.0, 200.0],
            "Jours bien-être accordés": [1, 0],
            "Éligible jours bien-être": [
                True,
                False,
            ],
        }
    )


def create_historical_activities() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "ID": [1, 2],
            "ID salarié": [1, 2],
        }
    )


def create_incremental_activities() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "ID": [3, 4],
            "ID salarié": [1, 2],
        }
    )


def create_slack_messages() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "ID activité": [3, 4],
            "Message Slack": [
                "Nouvelle activité 3",
                "Nouvelle activité 4",
            ],
        }
    )


def configure_common_pipeline_mocks(
    pipeline: Pipeline,
    employees: pd.DataFrame,
    slack_messages: pd.DataFrame,
) -> None:
    pipeline.extract_hr = Mock(
        return_value=pd.DataFrame()
    )

    pipeline.extract_sport = Mock(
        return_value=pd.DataFrame()
    )

    pipeline.transform = Mock(
        return_value=employees
    )

    pipeline.validate = Mock(
        return_value=employees
    )

    pipeline.compute_distance = Mock(
        return_value=employees
    )

    pipeline.compute_eligibility = Mock(
        return_value=employees
    )

    pipeline.compute_wellbeing = Mock(
        return_value=employees
    )

    pipeline.generate_slack_messages = Mock(
        return_value=slack_messages
    )

    pipeline.persist_data = Mock()

    pipeline.export = Mock()
    pipeline.export_activities = Mock()
    pipeline.export_slack_messages = Mock()
    pipeline.export_pipeline_runs = Mock()

    pipeline.repository.save_pipeline_run = Mock()


def test_first_run_generates_historical_data_without_sending_slack(
) -> None:
    pipeline = Pipeline()

    employees = create_employees()
    historical_activities = (
        create_historical_activities()
    )
    slack_messages = create_slack_messages()

    configure_common_pipeline_mocks(
        pipeline,
        employees,
        slack_messages,
    )

    pipeline.repository.activities_exist = Mock(
        return_value=False
    )

    pipeline.generate_activities = Mock(
        return_value=historical_activities
    )

    pipeline.generate_incremental_activities = Mock()

    pipeline.slack_webhook_service.send_messages = Mock()

    def read_table(
        table_name: str,
    ) -> pd.DataFrame:
        if (
            table_name
            == pipeline.repository.ACTIVITIES_TABLE
        ):
            return historical_activities

        if (
            table_name
            == pipeline.repository.SLACK_MESSAGES_TABLE
        ):
            return slack_messages

        return pd.DataFrame()

    pipeline.repository.read_table = Mock(
        side_effect=read_table
    )

    with patch(
        "etl.pipeline_service.validate_activities",
        side_effect=(
            lambda activities, employees: activities
        ),
    ):
        (
            result_employees,
            result_activities,
            result_messages,
        ) = pipeline.run()

    pipeline.generate_activities.assert_called_once_with(
        employees
    )

    pipeline.generate_incremental_activities.assert_not_called()

    pipeline.compute_wellbeing.assert_called_once()

    wellbeing_call = (
        pipeline.compute_wellbeing.call_args
    )

    assert wellbeing_call.args[0] is employees

    assert wellbeing_call.args[1].equals(
        historical_activities
    )

    pipeline.generate_slack_messages.assert_called_once_with(
        employees,
        historical_activities,
    )

    pipeline.slack_webhook_service.send_messages.assert_not_called()

    pipeline.persist_data.assert_called_once_with(
        employees=employees,
        activities=historical_activities,
        slack_messages=slack_messages,
        incremental_mode=False,
    )

    pipeline.export.assert_called_once_with(
        employees
    )

    pipeline.export_activities.assert_called_once_with(
        historical_activities
    )

    pipeline.export_slack_messages.assert_called_once_with(
        slack_messages
    )

    assert result_employees is employees

    assert result_activities.equals(
        historical_activities
    )

    assert result_messages.equals(
        slack_messages
    )


def test_incremental_run_generates_only_new_activities_and_sends_slack(
) -> None:
    pipeline = Pipeline()

    employees = create_employees()

    historical_activities = (
        create_historical_activities()
    )

    incremental_activities = (
        create_incremental_activities()
    )

    slack_messages = create_slack_messages()

    all_activities = pd.concat(
        [
            historical_activities,
            incremental_activities,
        ],
        ignore_index=True,
    )

    configure_common_pipeline_mocks(
        pipeline,
        employees,
        slack_messages,
    )

    pipeline.repository.activities_exist = Mock(
        return_value=True
    )

    pipeline.generate_activities = Mock()

    pipeline.generate_incremental_activities = Mock(
        return_value=incremental_activities
    )

    pipeline.slack_webhook_service.send_messages = Mock()

    activity_read_count = 0

    def read_table(
        table_name: str,
    ) -> pd.DataFrame:
        nonlocal activity_read_count

        if (
            table_name
            == pipeline.repository.ACTIVITIES_TABLE
        ):
            activity_read_count += 1

            # Première lecture :
            # historique avant la persistance.
            if activity_read_count == 1:
                return historical_activities

            # Deuxième lecture :
            # historique complet après la persistance.
            return all_activities

        if (
            table_name
            == pipeline.repository.SLACK_MESSAGES_TABLE
        ):
            return slack_messages

        return pd.DataFrame()

    pipeline.repository.read_table = Mock(
        side_effect=read_table
    )

    with patch(
        "etl.pipeline_service.validate_activities",
        side_effect=(
            lambda activities, employees: activities
        ),
    ):
        (
            result_employees,
            result_activities,
            result_messages,
        ) = pipeline.run()

    pipeline.generate_incremental_activities.assert_called_once_with(
        employees
    )

    pipeline.generate_activities.assert_not_called()

    pipeline.compute_wellbeing.assert_called_once()

    wellbeing_call = (
        pipeline.compute_wellbeing.call_args
    )

    assert wellbeing_call.args[0] is employees

    assert wellbeing_call.args[1].equals(
        all_activities
    )

    pipeline.generate_slack_messages.assert_called_once_with(
        employees,
        incremental_activities,
    )

    pipeline.slack_webhook_service.send_messages.assert_called_once_with(
        slack_messages
    )

    pipeline.persist_data.assert_called_once_with(
        employees=employees,
        activities=incremental_activities,
        slack_messages=slack_messages,
        incremental_mode=True,
    )

    pipeline.export.assert_called_once_with(
        employees
    )

    pipeline.export_activities.assert_called_once_with(
        all_activities
    )

    pipeline.export_slack_messages.assert_called_once_with(
        slack_messages
    )

    assert result_employees is employees

    assert result_activities.equals(
        all_activities
    )

    assert result_messages.equals(
        slack_messages
    )


def test_persist_data_uses_replace_for_first_run() -> None:
    pipeline = Pipeline()

    employees = create_employees()
    activities = create_historical_activities()
    slack_messages = create_slack_messages()

    pipeline.repository.save_employees = Mock(
        return_value=len(employees)
    )

    pipeline.repository.save_activities = Mock(
        return_value=len(activities)
    )

    pipeline.repository.save_slack_messages = Mock(
        return_value=len(slack_messages)
    )

    pipeline.repository.append_activities = Mock()
    pipeline.repository.append_slack_messages = Mock()

    pipeline.persist_data(
        employees=employees,
        activities=activities,
        slack_messages=slack_messages,
        incremental_mode=False,
    )

    pipeline.repository.save_employees.assert_called_once_with(
        employees
    )

    pipeline.repository.save_activities.assert_called_once_with(
        activities
    )

    pipeline.repository.save_slack_messages.assert_called_once_with(
        slack_messages
    )

    pipeline.repository.append_activities.assert_not_called()

    pipeline.repository.append_slack_messages.assert_not_called()


def test_persist_data_uses_append_for_incremental_run() -> None:
    pipeline = Pipeline()

    employees = create_employees()
    activities = create_incremental_activities()
    slack_messages = create_slack_messages()

    pipeline.repository.save_employees = Mock(
        return_value=len(employees)
    )

    pipeline.repository.append_activities = Mock(
        return_value=len(activities)
    )

    pipeline.repository.append_slack_messages = Mock(
        return_value=len(slack_messages)
    )

    pipeline.repository.save_activities = Mock()
    pipeline.repository.save_slack_messages = Mock()

    pipeline.persist_data(
        employees=employees,
        activities=activities,
        slack_messages=slack_messages,
        incremental_mode=True,
    )

    pipeline.repository.save_employees.assert_called_once_with(
        employees
    )

    pipeline.repository.append_activities.assert_called_once_with(
        activities
    )

    pipeline.repository.append_slack_messages.assert_called_once_with(
        slack_messages
    )

    pipeline.repository.save_activities.assert_not_called()

    pipeline.repository.save_slack_messages.assert_not_called()