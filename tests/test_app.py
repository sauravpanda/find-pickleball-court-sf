import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import asyncio
from src.app import PickleballCourtApp


class TestPickleballCourtApp:
    @pytest.fixture
    def mock_court_checker(self):
        mock = AsyncMock()
        mock.get_available_courts = AsyncMock(return_value=[])
        return mock

    @pytest.fixture
    def mock_slack_notifier(self):
        mock = MagicMock()
        mock.send_notification = MagicMock()
        return mock

    @pytest.fixture
    def mock_court_factory(self):
        with patch("src.court_factory.CourtFactory") as mock:
            mock.create_all_courts.return_value = [
                MagicMock(name="Buena Vista", url="https://www.rec.us/buenavista")
            ]
            yield mock

    @pytest.fixture
    def app(self, mock_court_checker, mock_slack_notifier, mock_court_factory):
        return PickleballCourtApp(
            court_checker=mock_court_checker, slack_notifier=mock_slack_notifier
        )

    @pytest.mark.asyncio
    async def test_run_checks_availability_and_sends_notification(
        self, app, mock_court_checker, mock_slack_notifier
    ):
        # Arrange
        mock_court_checker.get_available_courts.return_value = [
            {
                "court": "Buena Vista",
                "date": "2025-06-03",
                "time": "18:00",
                "available": True,
            }
        ]

        # Act
        await app.run()

        # Assert
        mock_court_checker.get_available_courts.assert_called_once()
        mock_slack_notifier.send_notification.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_with_no_availabilities(
        self, app, mock_court_checker, mock_slack_notifier
    ):
        # Arrange
        mock_court_checker.get_available_courts.return_value = []

        # Act
        await app.run()

        # Assert
        mock_court_checker.get_available_courts.assert_called_once()
        mock_slack_notifier.send_notification.assert_called_once_with([])

    @pytest.mark.asyncio
    async def test_run_with_specific_days_and_times(self, app, mock_court_checker):
        # Arrange
        app.days = ["Tuesday", "Thursday"]
        app.times = ["18:00", "19:00"]

        # Act
        await app.run()

        # Assert
        mock_court_checker.get_available_courts.assert_called_once_with(
            days=["Tuesday", "Thursday"], times=["18:00", "19:00"]
        )
