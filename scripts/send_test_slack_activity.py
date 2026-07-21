from __future__ import annotations

from datetime import datetime, timedelta

import pandas as pd

from config import (
    SLACK_TIMEOUT_SECONDS,
    SLACK_WEBHOOK_URL,
)
from database import (
    DataRepository,
    create_database_engine,
)
from services.live_activity_service import (
    LiveActivityService,
)
from services.slack_client import SlackClient
from services.slack_message_service import (
    SlackMessageService,
)


def main() -> None:
    if not SLACK_WEBHOOK_URL:
        raise RuntimeError(
            "La variable SLACK_WEBHOOK_URL "
            "doit être renseignée dans le fichier .env."
        )

    repository = DataRepository(
        create_database_engine()
    )

    employees = repository.read_table(
        repository.EMPLOYEES_TABLE
    )

    if employees.empty:
        raise RuntimeError(
            "La table employees est vide. "
            "Exécutez d'abord le pipeline."
        )

    employee = employees.iloc[0]

    started_at = pd.Timestamp(
        datetime.now()
    ).floor("s")

    activity = pd.DataFrame(
        [
            {
                "ID": "SLACK-DEMO-001",
                "ID salarié": employee["ID salarié"],
                "Date de début de l'activité": started_at,
                "Date de fin de l'activité": (
                    started_at
                    + timedelta(minutes=35)
                ),
                "Type": "Running",
                "Distance (m)": 5200,
                "Commentaire": (
                    "Activité live de démonstration"
                ),
            }
        ]
    )

    service = LiveActivityService(
        slack_message_service=SlackMessageService(),
        slack_client=SlackClient(
            webhook_url=SLACK_WEBHOOK_URL,
            timeout_seconds=SLACK_TIMEOUT_SECONDS,
        ),
    )

    message = service.publish(
        employees=employees,
        activity=activity,
    )

    print("Message envoyé avec succès :")
    print(message)


if __name__ == "__main__":
    main()