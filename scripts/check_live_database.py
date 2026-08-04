from __future__ import annotations

import pandas as pd
from sqlalchemy import text

from database import create_database_engine


def main() -> None:
    engine = create_database_engine()

    activities_query = text(
        """
        SELECT
            "ID",
            "ID salarié",
            "Date de début de l'activité",
            "Date de fin de l'activité",
            "Type",
            "Distance (m)",
            "Commentaire"
        FROM activities
        ORDER BY "ID" DESC
        LIMIT 10
        """
    )

    slack_messages_query = text(
        """
        SELECT
            "ID",
            "ID salarié",
            "Message Slack"
        FROM slack_messages
        ORDER BY "ID" DESC
        LIMIT 10
        """
    )

    activity_count_query = text(
        """
        SELECT COUNT(*)
        FROM activities
        """
    )

    slack_message_count_query = text(
        """
        SELECT COUNT(*)
        FROM slack_messages
        """
    )

    with engine.connect() as connection:
        activities = pd.read_sql(
            activities_query,
            connection,
        )

        slack_messages = pd.read_sql(
            slack_messages_query,
            connection,
        )

        activity_count = connection.execute(
            activity_count_query
        ).scalar_one()

        slack_message_count = connection.execute(
            slack_message_count_query
        ).scalar_one()

    print()
    print("=== ÉTAT DE SQLITE ===")
    print(f"Nombre total d'activités : {activity_count}")
    print(
        "Nombre total de messages Slack : "
        f"{slack_message_count}"
    )

    print()
    print("=== 10 DERNIÈRES ACTIVITÉS ===")

    if activities.empty:
        print("Aucune activité trouvée.")
    else:
        print(
            activities.to_string(
                index=False,
            )
        )

    print()
    print("=== 10 DERNIERS MESSAGES SLACK ===")

    if slack_messages.empty:
        print("Aucun message Slack trouvé.")
    else:
        print(
            slack_messages.to_string(
                index=False,
            )
        )


if __name__ == "__main__":
    main()