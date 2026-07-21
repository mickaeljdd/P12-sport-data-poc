from unittest.mock import Mock, patch

import pytest

from services.slack_client import SlackClient


def test_rejects_empty_webhook_url():
    with pytest.raises(
        ValueError,
        match="webhook Slack est absente",
    ):
        SlackClient("")


def test_rejects_invalid_webhook_url():
    with pytest.raises(
        ValueError,
        match="webhook Slack est invalide",
    ):
        SlackClient("https://example.com/webhook")


@patch("services.slack_client.requests.post")
def test_sends_message(mock_post):
    response = Mock()
    response.text = "ok"
    response.raise_for_status.return_value = None
    mock_post.return_value = response

    client = SlackClient(
        "https://hooks.slack.com/services/test/test/test"
    )

    client.send_message("Bonjour Slack")

    mock_post.assert_called_once_with(
        "https://hooks.slack.com/services/test/test/test",
        json={"text": "Bonjour Slack"},
        timeout=10,
    )