from __future__ import annotations

import pandas as pd

from services.slack_client import SlackClient
from services.slack_message_service import (
    SlackMessageService,
)


class LiveActivityService:
    """
    Génère et envoie le message Slack associé
    à une seule nouvelle activité.
    """

    def __init__(
        self,
        slack_message_service: SlackMessageService,
        slack_client: SlackClient,
    ) -> None:
        self.slack_message_service = (
            slack_message_service
        )
        self.slack_client = slack_client

    def publish(
        self,
        employees: pd.DataFrame,
        activity: pd.DataFrame,
    ) -> str:
        if len(activity) != 1:
            raise ValueError(
                "Une seule activité live doit être fournie."
            )

        messages = (
            self.slack_message_service.generate(
                employees,
                activity,
            )
        )

        message = str(
            messages.iloc[0]["Message Slack"]
        )

        self.slack_client.send_message(message)

        return message