from __future__ import annotations

from pprint import pprint

from streaming.config import StreamingSettings
from streaming.consumer import RedpandaConsumer


def main() -> None:
    settings = StreamingSettings.from_env()
    RedpandaConsumer(
        topic=settings.monitoring_topic,
        bootstrap_servers=settings.bootstrap_servers,
        group_id="sport-monitoring-console",
        handler=pprint,
    ).run()


if __name__ == "__main__":
    main()
