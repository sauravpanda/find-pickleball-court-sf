import pytest
from unittest.mock import patch, MagicMock
from src.slack_notifier import SlackNotifier


class TestSlackNotifier:
    @pytest.fixture
    def mock_slack_client(self):
        with patch("slack_sdk.WebClient") as mock_client:
            mock_instance = MagicMock()
            mock_client.return_value = mock_instance
            yield mock_instance

    @pytest.fixture
    def notifier(self, mock_slack_client):
        with patch("os.getenv") as mock_getenv:
            mock_getenv.side_effect = lambda key: {
                "SLACK_API_TOKEN": "test-token",
                "SLACK_CHANNEL": "test-channel",
            }.get(key)
            return SlackNotifier()

    def test_init_loads_config_from_env(self):
        # Arrange
        with patch("os.getenv") as mock_getenv:
            mock_getenv.side_effect = lambda key: {
                "SLACK_API_TOKEN": "test-token",
                "SLACK_CHANNEL": "test-channel",
            }.get(key)

            # Act
            notifier = SlackNotifier()

            # Assert
            assert notifier.channel == "test-channel"
            mock_getenv.assert_any_call("SLACK_API_TOKEN")
            mock_getenv.assert_any_call("SLACK_CHANNEL")

    def test_send_notification_calls_slack_api(self, notifier, mock_slack_client):
        # Arrange
        availabilities = [
            {
                "court": "Buena Vista",
                "date": "2025-06-03",
                "time": "18:00",
                "available": True,
            }
        ]

        # Act
        notifier.send_notification(availabilities)

        # Assert
        mock_slack_client.chat_postMessage.assert_called_once()
        call_args = mock_slack_client.chat_postMessage.call_args[1]
        assert call_args["channel"] == "test-channel"
        assert "Buena Vista" in call_args["text"]
        assert "2025-06-03" in call_args["text"]
        assert "18:00" in call_args["text"]

    def test_format_message_creates_readable_message(self, notifier):
        # Arrange
        availabilities = [
            {
                "court": "Buena Vista",
                "date": "2025-06-03",
                "time": "18:00",
                "available": True,
            },
            {
                "court": "Richmond",
                "date": "2025-06-05",
                "time": "19:00",
                "available": True,
            },
        ]

        # Act
        message = notifier.format_message(availabilities)

        # Assert
        assert "Available Pickleball Courts" in message
        assert "Buena Vista" in message
        assert "2025-06-03" in message
        assert "18:00" in message
        assert "Richmond" in message
        assert "2025-06-05" in message
        assert "19:00" in message

    def test_format_message_handles_empty_list(self, notifier):
        # Arrange
        availabilities = []

        # Act
        message = notifier.format_message(availabilities)

        # Assert
        assert "No available courts found" in message
