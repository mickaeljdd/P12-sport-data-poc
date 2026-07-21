from __future__ import annotations

import requests


class SlackClient:
    """
    Envoie un message vers Slack à l'aide d'un Incoming Webhook.
    """

    def __init__(
        self,
        webhook_url: str,
        timeout_seconds: int = 10,
    ) -> None:
        webhook_url = str(webhook_url).strip()

        if not webhook_url:
            raise ValueError(
                "L'URL du webhook Slack est absente."
            )

        if not webhook_url.startswith(
            "https://hooks.slack.com/services/"
        ):
            raise ValueError(
                "L'URL du webhook Slack est invalide."
            )

        self.webhook_url = webhook_url
        self.timeout_seconds = timeout_seconds

    def send_message(
        self,
        message: str,
    ) -> None:
        message = str(message).strip()

        if not message:
            raise ValueError(
                "Le message Slack ne peut pas être vide."
            )

        response = requests.post(
            self.webhook_url,
            json={"text": message},
            timeout=self.timeout_seconds,
        )

        response.raise_for_status()

        if response.text.strip().lower() != "ok":
            raise RuntimeError(
                "Slack a retourné une réponse inattendue : "
                f"{response.text}"
            )