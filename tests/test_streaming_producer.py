import pandas as pd

from streaming.config import StreamingSettings
from streaming.producer import RedpandaProducer


class FakeFuture:
    def get(self, timeout):
        return None


class FakeKafkaProducer:
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.sent = []
        self.flushed = False
        self.closed = False

    def send(self, topic, key, value):
        self.sent.append((topic, key, value))
        return FakeFuture()

    def flush(self, timeout):
        self.flushed = True

    def close(self, timeout):
        self.closed = True


def settings():
    return StreamingSettings(
        enabled=True,
        bootstrap_servers="localhost:19092",
        client_id="test",
        activities_topic="sport.activities",
        slack_topic="sport.slack",
        monitoring_topic="sport.monitoring",
    )


def test_publish_dataframe_emits_one_event_per_row():
    producer = RedpandaProducer(settings(), producer_factory=FakeKafkaProducer)
    dataframe = pd.DataFrame([{"ID": 1, "Type": "Running"}, {"ID": 2, "Type": "Tennis"}])

    count = producer.publish_dataframe(
        "sport.activities", dataframe, key_column="ID", event_type="activity.created"
    )

    assert count == 2
    assert [item[1] for item in producer._producer.sent] == [1, 2]
    assert producer._producer.sent[0][2]["event_type"] == "activity.created"
    assert producer._producer.flushed is True


def test_publish_dataframe_rejects_missing_key_column():
    producer = RedpandaProducer(settings(), producer_factory=FakeKafkaProducer)

    try:
        producer.publish_dataframe("topic", pd.DataFrame([{"x": 1}]), "ID", "event")
    except ValueError as error:
        assert "ID" in str(error)
    else:
        raise AssertionError("ValueError attendu")
