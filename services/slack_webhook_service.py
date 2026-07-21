from __future__ import annotations

import logging

import pandas as pd
import requests

from config import (
    SLACK_TIMEOUT_SECONDS,
    SLACK_WEBHOOK_URL,
)


logger = logging.getLogger(__name__)


class SlackWebhookService:
    """Envoie les messages générés vers un webhook Slack."""

    def __init__(
        self,
        webhook_url: str | None = SLACK_WEBHOOK_URL,
        timeout_seconds: int = SLACK_TIMEOUT_SECONDS,
    ) -> None:
        self.webhook_url = webhook_url
        self.timeout_seconds = timeout_seconds

    def send_messages(
        self,
        messages: pd.DataFrame,
    ) -> int:
        if messages.empty:
            return 0

        if not self.webhook_url:
            logger.warning(
                "Envoi Slack ignoré : "
                "SLACK_WEBHOOK_URL non configurée."
            )
            return 0

        if "Message Slack" not in messages.columns:
            raise ValueError(
                "La colonne 'Message Slack' est absente."
            )

        sent_count = 0

        for message in messages["Message Slack"]:
            response = requests.post(
                self.webhook_url,
                json={"text": str(message)},
                timeout=self.timeout_seconds,
            )

            response.raise_for_status()
            sent_count += 1

        logger.info(
            "Messages Slack envoyés : %s",
            sent_count,
        )

        return sent_count