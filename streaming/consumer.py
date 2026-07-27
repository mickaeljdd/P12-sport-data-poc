from __future__ import annotations

import json
import signal
from collections.abc import Callable
from typing import Any

try:
    from kafka import KafkaConsumer as _KafkaConsumer
except ImportError:  # dépendance optionnelle quand le streaming est désactivé
    _KafkaConsumer = None


class RedpandaConsumer:
    """Boucle générique de consommation avec commit après traitement."""

    def __init__(
        self,
        topic: str,
        bootstrap_servers: str,
        group_id: str,
        handler: Callable[[dict[str, Any]], None],
    ) -> None:
        self.handler = handler
        self.running = True
        if _KafkaConsumer is None:
            raise RuntimeError(
                "Le package kafka-python-ng est requis pour consommer Redpanda."
            )
        self.consumer = _KafkaConsumer(
            topic,
            bootstrap_servers=bootstrap_servers,
            group_id=group_id,
            auto_offset_reset="earliest",
            enable_auto_commit=False,
            value_deserializer=lambda value: json.loads(value.decode("utf-8")),
        )

    def stop(self, *_: object) -> None:
        self.running = False

    def run(self) -> None:
        signal.signal(signal.SIGINT, self.stop)
        signal.signal(signal.SIGTERM, self.stop)
        try:
            while self.running:
                records = self.consumer.poll(timeout_ms=1000)
                for messages in records.values():
                    for message in messages:
                        self.handler(message.value)
                        self.consumer.commit()
        finally:
            self.consumer.close()
