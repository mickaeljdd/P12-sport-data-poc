from __future__ import annotations

from typing import Any

from config import (
    SLACK_TIMEOUT_SECONDS,
    SLACK_WEBHOOK_URL,
)
from monitoring.logger import logger
from services.slack_client import SlackClient
from streaming.config import StreamingSettings
from streaming.consumer import RedpandaConsumer


SLACK_EVENT_TYPE = "slack.message.created"
SLACK_CONSUMER_GROUP_ID = "sport-slack-consumer"


def extract_slack_message(
    event: dict[str, Any],
) -> str:
    """
    Valide un événement Redpanda et retourne le texte Slack.

    Format attendu :

    {
        "event_type": "slack.message.created",
        "payload": {
            "ID": ...,
            "ID salarié": ...,
            "Message Slack": "..."
        }
    }
    """
    if not isinstance(event, dict):
        raise ValueError(
            "L'événement Redpanda doit être un dictionnaire."
        )

    event_type = event.get("event_type")

    if event_type != SLACK_EVENT_TYPE:
        raise ValueError(
            "Type d'événement inattendu : "
            f"{event_type!r}. "
            f"Type attendu : {SLACK_EVENT_TYPE!r}."
        )

    payload = event.get("payload")

    if not isinstance(payload, dict):
        raise ValueError(
            "Le champ payload est absent ou invalide."
        )

    message = str(
        payload.get("Message Slack", "")
    ).strip()

    if not message:
        raise ValueError(
            "Le champ 'Message Slack' est absent ou vide."
        )

    return message


def main() -> None:
    settings = StreamingSettings.from_env()

    if not settings.enabled:
        raise RuntimeError(
            "Le streaming est désactivé. "
            "Définissez STREAMING_ENABLED=true."
        )

    slack_client = SlackClient(
        webhook_url=SLACK_WEBHOOK_URL,
        timeout_seconds=SLACK_TIMEOUT_SECONDS,
    )

    logger.info(
        "Démarrage du consommateur Slack "
        "| topic=%s "
        "| groupe=%s "
        "| brokers=%s",
        settings.slack_topic,
        SLACK_CONSUMER_GROUP_ID,
        settings.bootstrap_servers,
    )

    def handle(
        event: dict[str, Any],
    ) -> None:
        logger.info(
            "Événement reçu depuis Redpanda "
            "| event_type=%s",
            event.get("event_type"),
        )

        try:
            message = extract_slack_message(event)

            logger.info(
                "Envoi du message vers Slack "
                "| longueur=%s caractère(s)",
                len(message),
            )

            slack_client.send_message(message)

            logger.info(
                "Message Slack envoyé avec succès."
            )

        except Exception:
            logger.exception(
                "Échec du traitement de l'événement Slack "
                "| événement=%r",
                event,
            )

            # L'exception est propagée afin que RedpandaConsumer
            # ne valide pas l'offset du message en échec.
            raise

    consumer = RedpandaConsumer(
        topic=settings.slack_topic,
        bootstrap_servers=settings.bootstrap_servers,
        group_id=SLACK_CONSUMER_GROUP_ID,
        handler=handle,
    )

    try:
        consumer.run()
    except KeyboardInterrupt:
        logger.info(
            "Arrêt manuel du consommateur Slack."
        )
    except Exception:
        logger.exception(
            "Le consommateur Slack s'est arrêté à cause "
            "d'une erreur."
        )
        raise
    finally:
        logger.info(
            "Consommateur Slack arrêté."
        )


if __name__ == "__main__":
    main()