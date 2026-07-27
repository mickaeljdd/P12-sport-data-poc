from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class StreamingSettings:
    enabled: bool
    bootstrap_servers: str
    client_id: str
    activities_topic: str
    slack_topic: str
    monitoring_topic: str

    @classmethod
    def from_env(cls) -> "StreamingSettings":
        return cls(
            enabled=os.getenv("STREAMING_ENABLED", "false").strip().lower()
            in {"1", "true", "yes", "on"},
            bootstrap_servers=os.getenv(
                "REDPANDA_BOOTSTRAP_SERVERS", "localhost:19092"
            ).strip(),
            client_id=os.getenv("REDPANDA_CLIENT_ID", "sport-data-poc").strip(),
            activities_topic=os.getenv(
                "REDPANDA_ACTIVITIES_TOPIC", "sport.activities"
            ).strip(),
            slack_topic=os.getenv("REDPANDA_SLACK_TOPIC", "sport.slack").strip(),
            monitoring_topic=os.getenv(
                "REDPANDA_MONITORING_TOPIC", "sport.monitoring"
            ).strip(),
        )
