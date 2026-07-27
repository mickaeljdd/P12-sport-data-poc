from __future__ import annotations

import json
from typing import Any, Callable

import pandas as pd
try:
    from kafka import KafkaProducer as _KafkaProducer
except ImportError:  # dépendance optionnelle quand le streaming est désactivé
    _KafkaProducer = None

from streaming.config import StreamingSettings
from streaming.serialization import dataframe_records


class RedpandaProducer:
    """Publie des événements JSON dans Redpanda via l'API Kafka."""

    def __init__(
        self,
        settings: StreamingSettings | None = None,
        producer_factory: Callable[..., Any] | None = None,
    ) -> None:
        self.settings = settings or StreamingSettings.from_env()
        factory = producer_factory or _KafkaProducer
        if factory is None:
            raise RuntimeError(
                "Le package kafka-python-ng est requis pour activer Redpanda."
            )
        self._producer = factory(
            bootstrap_servers=self.settings.bootstrap_servers,
            client_id=self.settings.client_id,
            value_serializer=lambda value: json.dumps(
                value, ensure_ascii=False
            ).encode("utf-8"),
            key_serializer=lambda key: str(key).encode("utf-8"),
            acks="all",
            retries=5,
        )

    def publish(self, topic: str, event: dict[str, Any], key: Any) -> None:
        future = self._producer.send(topic, key=key, value=event)
        future.get(timeout=10)

    def publish_dataframe(
        self,
        topic: str,
        dataframe: pd.DataFrame,
        key_column: str,
        event_type: str,
    ) -> int:
        if key_column not in dataframe.columns:
            raise ValueError(f"Colonne de clé absente : {key_column}")

        count = 0
        for record in dataframe_records(dataframe):
            key = record[key_column]
            self.publish(
                topic,
                {"event_type": event_type, "payload": record},
                key=key,
            )
            count += 1
        self.flush()
        return count

    def flush(self) -> None:
        self._producer.flush(timeout=10)

    def close(self) -> None:
        self._producer.close(timeout=10)

    def __enter__(self) -> "RedpandaProducer":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()
