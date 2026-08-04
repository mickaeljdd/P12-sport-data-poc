from unittest.mock import Mock, patch

import pandas as pd
from pandas.testing import assert_frame_equal

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
            "Date de début de l'activité": [
                "2026-01-10 08:00:00",
                "2026-01-11 09:00:00",
            ],
            "Type": [
                "Runing",
                "Natation",
            ],
            "Distance (m)": [
                5000,
                1500,
            ],
            "Date de fin de l'activité": [
                "2026-01-10 08:40:00",
                "2026-01-11 09:45:00",
            ],
            "Commentaire": [
                "Sortie historique",
                "Séance historique",
            ],
        }
    )


def create_incremental_activities() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "ID": [3, 4],
            "ID salarié": [1, 2],
            "Date de début de l'activité": [
                "2026-01-12 08:00:00",
                "2026-01-12 10:00:00",
            ],
            "Type": [
                "Runing",
                "Natation",
            ],
            "Distance (m)": [
                6000,
                1800,
            ],
            "Date de fin de l'activité": [
                "2026-01-12 08:45:00",
                "2026-01-12 10:50:00",
            ],
            "Commentaire": [
                "Nouvelle sortie",
                "Nouvelle séance",
            ],
        }
    )


def create_slack_messages(
    activity_ids: list[int],
) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "ID": activity_ids,
            "ID salarié": [1, 2],
            "Message Slack": [
                f"Nouvelle activité {activity_ids[0]}",
                f"Nouvelle activité {activity_ids[1]}",
            ],
        }
    )


def configure_common_pipeline_mocks(
    pipeline: Pipeline,
    employees: pd.DataFrame,
    slack_messages: pd.DataFrame,
) -> None:
    """
    Remplace toutes les dépendances externes afin de conserver
    des tests unitaires sans accès aux fichiers, à SQLite ou à Redpanda.
    """

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

    # Évite toute connexion réelle à Kafka/Redpanda.
    pipeline.publish_streaming_events = Mock()

    # Évite toute écriture réelle dans SQLite.
    pipeline.repository.save_employees = Mock()
    pipeline.repository.save_activities = Mock()
    pipeline.repository.append_activities = Mock()
    pipeline.repository.save_slack_messages = Mock()
    pipeline.repository.append_slack_messages = Mock()
    pipeline.repository.save_pipeline_run = Mock()

    # Évite les exports CSV réels.
    pipeline.export = Mock()
    pipeline.export_activities = Mock()
    pipeline.export_slack_messages = Mock()
    pipeline.export_pipeline_runs = Mock()


def test_first_run_generates_historical_data_without_sending_slack(
) -> None:
    pipeline = Pipeline()

    employees = create_employees()
    historical_activities = create_historical_activities()
    slack_messages = create_slack_messages([1, 2])

    configure_common_pipeline_mocks(
        pipeline=pipeline,
        employees=employees,
        slack_messages=slack_messages,
    )

    pipeline.repository.activities_exist = Mock(
        return_value=False
    )

    pipeline.generate_activities = Mock(
        return_value=historical_activities
    )

    pipeline.generate_incremental_activities = Mock()

    def read_table(
        table_name: str,
    ) -> pd.DataFrame:
        if (
            table_name
            == pipeline.repository.SLACK_MESSAGES_TABLE
        ):
            return slack_messages.copy()

        if (
            table_name
            == pipeline.repository.ACTIVITIES_TABLE
        ):
            return historical_activities.copy()

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

    # Le premier lancement utilise le générateur historique.
    pipeline.generate_activities.assert_called_once_with(
        employees
    )

    pipeline.generate_incremental_activities.assert_not_called()

    # Le bien-être est calculé avec les activités historiques.
    pipeline.compute_wellbeing.assert_called_once()

    wellbeing_call = pipeline.compute_wellbeing.call_args

    assert wellbeing_call.args[0] is employees

    assert_frame_equal(
        wellbeing_call.args[1].reset_index(drop=True),
        historical_activities.reset_index(drop=True),
        check_dtype=False,
    )

    # Les messages sont générés à partir des activités historiques.
    pipeline.generate_slack_messages.assert_called_once()

    slack_generation_call = (
        pipeline.generate_slack_messages.call_args
    )

    assert slack_generation_call.args[0] is employees

    assert_frame_equal(
        slack_generation_call.args[1].reset_index(
            drop=True
        ),
        historical_activities.reset_index(drop=True),
        check_dtype=False,
    )

    # Les activités historiques remplacent la table.
    pipeline.repository.save_activities.assert_called_once()

    saved_activities = (
        pipeline.repository.save_activities.call_args.args[0]
    )

    assert_frame_equal(
        saved_activities.reset_index(drop=True),
        historical_activities.reset_index(drop=True),
        check_dtype=False,
    )

    pipeline.repository.append_activities.assert_not_called()

    # Les salariés enrichis sont enregistrés.
    pipeline.repository.save_employees.assert_called_once()

    saved_employees = (
        pipeline.repository.save_employees.call_args.args[0]
    )

    assert_frame_equal(
        saved_employees.reset_index(drop=True),
        employees.reset_index(drop=True),
        check_dtype=False,
    )

    # Les messages initiaux remplacent la table Slack.
    pipeline.repository.save_slack_messages.assert_called_once()

    saved_messages = (
        pipeline.repository.save_slack_messages
        .call_args.args[0]
    )

    assert_frame_equal(
        saved_messages.reset_index(drop=True),
        slack_messages.reset_index(drop=True),
        check_dtype=False,
    )

    pipeline.repository.append_slack_messages.assert_not_called()

    # Vérification des exports.
    pipeline.export.assert_called_once()

    exported_employees = pipeline.export.call_args.args[0]

    assert_frame_equal(
        exported_employees.reset_index(drop=True),
        employees.reset_index(drop=True),
        check_dtype=False,
    )

    pipeline.export_activities.assert_called_once()

    exported_activities = (
        pipeline.export_activities.call_args.args[0]
    )

    assert_frame_equal(
        exported_activities.reset_index(drop=True),
        historical_activities.reset_index(drop=True),
        check_dtype=False,
    )

    pipeline.export_slack_messages.assert_called_once()

    exported_messages = (
        pipeline.export_slack_messages.call_args.args[0]
    )

    assert_frame_equal(
        exported_messages.reset_index(drop=True),
        slack_messages.reset_index(drop=True),
        check_dtype=False,
    )

    # Le monitoring Redpanda peut être publié,
    # mais pas les événements métier historiques.
    pipeline.publish_streaming_events.assert_called_once()

    streaming_call = (
        pipeline.publish_streaming_events.call_args
    )

    assert (
        streaming_call.kwargs[
            "publish_business_events"
        ]
        is False
    )

    assert_frame_equal(
        streaming_call.kwargs[
            "activities"
        ].reset_index(drop=True),
        historical_activities.reset_index(drop=True),
        check_dtype=False,
    )

    assert_frame_equal(
        streaming_call.kwargs[
            "slack_messages"
        ].reset_index(drop=True),
        slack_messages.reset_index(drop=True),
        check_dtype=False,
    )

    # Vérification des résultats retournés.
    assert result_employees is employees

    assert_frame_equal(
        result_activities.reset_index(drop=True),
        historical_activities.reset_index(drop=True),
        check_dtype=False,
    )

    assert_frame_equal(
        result_messages.reset_index(drop=True),
        slack_messages.reset_index(drop=True),
        check_dtype=False,
    )


def test_incremental_run_generates_only_new_activities_and_sends_slack(
) -> None:
    pipeline = Pipeline()

    employees = create_employees()
    historical_activities = create_historical_activities()
    incremental_activities = create_incremental_activities()
    slack_messages = create_slack_messages([3, 4])

    all_activities = pd.concat(
        [
            historical_activities,
            incremental_activities,
        ],
        ignore_index=True,
    )

    configure_common_pipeline_mocks(
        pipeline=pipeline,
        employees=employees,
        slack_messages=slack_messages,
    )

    pipeline.repository.activities_exist = Mock(
        return_value=True
    )

    pipeline.generate_activities = Mock()

    pipeline.generate_incremental_activities = Mock(
        return_value=incremental_activities
    )

    def read_table(
        table_name: str,
    ) -> pd.DataFrame:
        # Dans Pipeline.run(), cette lecture intervient après
        # append_activities(). Elle doit donc renvoyer l'historique
        # complet, incluant les nouvelles activités.
        if (
            table_name
            == pipeline.repository.ACTIVITIES_TABLE
        ):
            return all_activities.copy()

        if (
            table_name
            == pipeline.repository.SLACK_MESSAGES_TABLE
        ):
            return slack_messages.copy()

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

    # Le mode incrémental est utilisé.
    pipeline.generate_incremental_activities.assert_called_once_with(
        employees
    )

    pipeline.generate_activities.assert_not_called()

    # Seules les nouvelles activités sont ajoutées.
    pipeline.repository.append_activities.assert_called_once()

    appended_activities = (
        pipeline.repository.append_activities
        .call_args.args[0]
    )

    assert_frame_equal(
        appended_activities.reset_index(drop=True),
        incremental_activities.reset_index(drop=True),
        check_dtype=False,
    )

    pipeline.repository.save_activities.assert_not_called()

    # Le bien-être est recalculé avec tout l'historique.
    pipeline.compute_wellbeing.assert_called_once()

    wellbeing_call = pipeline.compute_wellbeing.call_args

    assert wellbeing_call.args[0] is employees

    assert_frame_equal(
        wellbeing_call.args[1].reset_index(drop=True),
        all_activities.reset_index(drop=True),
        check_dtype=False,
    )

    # Les messages Slack concernent uniquement
    # les nouvelles activités.
    pipeline.generate_slack_messages.assert_called_once()

    slack_generation_call = (
        pipeline.generate_slack_messages.call_args
    )

    assert slack_generation_call.args[0] is employees

    assert_frame_equal(
        slack_generation_call.args[1].reset_index(
            drop=True
        ),
        incremental_activities.reset_index(drop=True),
        check_dtype=False,
    )

    # Les salariés recalculés sont enregistrés.
    pipeline.repository.save_employees.assert_called_once()

    saved_employees = (
        pipeline.repository.save_employees.call_args.args[0]
    )

    assert_frame_equal(
        saved_employees.reset_index(drop=True),
        employees.reset_index(drop=True),
        check_dtype=False,
    )

    # Les nouveaux messages Slack sont ajoutés.
    pipeline.repository.append_slack_messages.assert_called_once()

    appended_messages = (
        pipeline.repository.append_slack_messages
        .call_args.args[0]
    )

    assert_frame_equal(
        appended_messages.reset_index(drop=True),
        slack_messages.reset_index(drop=True),
        check_dtype=False,
    )

    pipeline.repository.save_slack_messages.assert_not_called()

    # Les exports utilisent les données complètes.
    pipeline.export.assert_called_once()

    exported_employees = pipeline.export.call_args.args[0]

    assert_frame_equal(
        exported_employees.reset_index(drop=True),
        employees.reset_index(drop=True),
        check_dtype=False,
    )

    pipeline.export_activities.assert_called_once()

    exported_activities = (
        pipeline.export_activities.call_args.args[0]
    )

    assert_frame_equal(
        exported_activities.reset_index(drop=True),
        all_activities.reset_index(drop=True),
        check_dtype=False,
    )

    pipeline.export_slack_messages.assert_called_once()

    exported_messages = (
        pipeline.export_slack_messages.call_args.args[0]
    )

    assert_frame_equal(
        exported_messages.reset_index(drop=True),
        slack_messages.reset_index(drop=True),
        check_dtype=False,
    )

    # Les événements métier sont publiés en incrémental.
    pipeline.publish_streaming_events.assert_called_once()

    streaming_call = (
        pipeline.publish_streaming_events.call_args
    )

    assert (
        streaming_call.kwargs[
            "publish_business_events"
        ]
        is True
    )

    assert_frame_equal(
        streaming_call.kwargs[
            "activities"
        ].reset_index(drop=True),
        incremental_activities.reset_index(drop=True),
        check_dtype=False,
    )

    assert_frame_equal(
        streaming_call.kwargs[
            "slack_messages"
        ].reset_index(drop=True),
        slack_messages.reset_index(drop=True),
        check_dtype=False,
    )

    # Vérification des résultats retournés.
    assert result_employees is employees

    assert_frame_equal(
        result_activities.reset_index(drop=True),
        all_activities.reset_index(drop=True),
        check_dtype=False,
    )

    assert_frame_equal(
        result_messages.reset_index(drop=True),
        slack_messages.reset_index(drop=True),
        check_dtype=False,
    )