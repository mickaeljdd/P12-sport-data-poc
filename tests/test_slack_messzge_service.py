import pandas as pd
import pytest

from services.slack_message_service import (
    SlackMessageService,
)


def build_employees() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "ID salarié": [
                43015,
                35731,
                99999,
            ],
            "Prénom": [
                "Juliette",
                "Laurence",
                "Paul",
            ],
            "Nom": [
                "Mendes",
                "Morvan",
                "Martin",
            ],
        }
    )


def build_activities() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "ID": [1, 2, 3],
            "ID salarié": [
                43015,
                35731,
                99999,
            ],
            "Date de début de l'activité": (
                pd.to_datetime(
                    [
                        "2025-01-10 09:00:00",
                        "2025-01-11 10:00:00",
                        "2025-01-12 18:00:00",
                    ]
                )
            ),
            "Date de fin de l'activité": (
                pd.to_datetime(
                    [
                        "2025-01-10 09:46:00",
                        "2025-01-11 12:30:00",
                        "2025-01-12 19:15:00",
                    ]
                )
            ),
            "Type": [
                "Runing",
                "Randonnée",
                "Escalade",
            ],
            "Distance (m)": [
                10800,
                10000,
                None,
            ],
            "Commentaire": [
                "",
                (
                    "Randonnée de Saint-Guilhem-le-Désert, "
                    "je vous la conseille"
                ),
                None,
            ],
        }
    )


def test_generates_one_message_per_activity():
    service = SlackMessageService()

    result = service.generate(
        build_employees(),
        build_activities(),
    )

    assert len(result) == 3
    assert result["Message Slack"].notna().all()


def test_running_message_contains_distance_and_duration():
    service = SlackMessageService()

    result = service.generate(
        build_employees(),
        build_activities(),
    )

    message = result.loc[
        result["ID"] == 1,
        "Message Slack",
    ].iloc[0]

    assert "Juliette Mendes" in message
    assert "10,8 km" in message
    assert "46 min" in message
    assert "courir" in message


def test_hiking_message_contains_comment():
    service = SlackMessageService()

    result = service.generate(
        build_employees(),
        build_activities(),
    )

    message = result.loc[
        result["ID"] == 2,
        "Message Slack",
    ].iloc[0]

    assert "Laurence Morvan" in message
    assert "10,0 km" in message
    assert "Saint-Guilhem-le-Désert" in message


def test_activity_without_distance_uses_duration():
    service = SlackMessageService()

    result = service.generate(
        build_employees(),
        build_activities(),
    )

    message = result.loc[
        result["ID"] == 3,
        "Message Slack",
    ].iloc[0]

    assert "Paul Martin" in message
    assert "Escalade" in message
    assert "75 min" in message
    assert "km" not in message


def test_result_has_expected_columns():
    service = SlackMessageService()

    result = service.generate(
        build_employees(),
        build_activities(),
    )

    assert list(result.columns) == [
        "ID",
        "ID salarié",
        "Date de début de l'activité",
        "Message Slack",
    ]


def test_original_dataframes_are_not_modified():
    employees = build_employees()
    activities = build_activities()

    original_employees = employees.copy(
        deep=True
    )

    original_activities = activities.copy(
        deep=True
    )

    service = SlackMessageService()

    service.generate(
        employees,
        activities,
    )

    pd.testing.assert_frame_equal(
        employees,
        original_employees,
    )

    pd.testing.assert_frame_equal(
        activities,
        original_activities,
    )


def test_unknown_employee_raises_error():
    employees = build_employees()

    activities = build_activities().copy()

    activities.loc[
        activities["ID"] == 1,
        "ID salarié",
    ] = 123456

    service = SlackMessageService()

    with pytest.raises(
        ValueError,
        match="aucun salarié",
    ):
        service.generate(
            employees,
            activities,
        )


def test_invalid_dates_raise_error():
    activities = build_activities().copy()

    activities.loc[
        activities["ID"] == 1,
        "Date de fin de l'activité",
    ] = pd.Timestamp(
        "2025-01-10 08:00:00"
    )

    service = SlackMessageService()

    with pytest.raises(
        ValueError,
        match="date de fin",
    ):
        service.generate(
            build_employees(),
            activities,
        )


def test_missing_employee_column_raises_error():
    employees = build_employees().drop(
        columns=["Prénom"]
    )

    service = SlackMessageService()

    with pytest.raises(
        ValueError,
        match="Colonnes salariés manquantes",
    ):
        service.generate(
            employees,
            build_activities(),
        )


def test_missing_activity_column_raises_error():
    activities = build_activities().drop(
        columns=["Commentaire"]
    )

    service = SlackMessageService()

    with pytest.raises(
        ValueError,
        match="Colonnes activités manquantes",
    ):
        service.generate(
            build_employees(),
            activities,
        )