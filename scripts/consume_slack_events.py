from __future__ import annotations

from config import SLACK_TIMEOUT_SECONDS, SLACK_WEBHOOK_URL
from services.slack_client import SlackClient
from streaming.config import StreamingSettings
from streaming.consumer import RedpandaConsumer


def main() -> None:
    settings = StreamingSettings.from_env()
    client = SlackClient(SLACK_WEBHOOK_URL, SLACK_TIMEOUT_SECONDS)

    def handle(event: dict) -> None:
        payload = event.get("payload", {})
        client.send_message(str(payload["Message Slack"]))

    RedpandaConsumer(
        topic=settings.slack_topic,
        bootstrap_servers=settings.bootstrap_servers,
        group_id="sport-slack-consumer",
        handler=handle,
    ).run()


if __name__ == "__main__":
    main()
