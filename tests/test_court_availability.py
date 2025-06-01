import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import datetime
from src.court_availability import CourtAvailabilityChecker, Court
from src.court_factory import CourtFactory


class TestCourtAvailabilityChecker:
    @pytest.fixture
    def mock_agent(self):
        mock = AsyncMock()
        mock.run = AsyncMock()
        mock.get_memory = AsyncMock(return_value={"court_availability": []})
        return mock

    @pytest.fixture
    def checker(self, mock_agent):
        return CourtAvailabilityChecker(agent=mock_agent)

    @pytest.mark.asyncio
    async def test_check_availability_calls_agent_run(self, checker, mock_agent):
        # Arrange
        court = Court(name="Buena Vista", url="https://www.rec.us/buenavista")

        # Act
        await checker.check_availability(court, ["Tuesday"], ["18:00", "19:00"])

        # Assert
        mock_agent.run.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_available_courts_returns_list(self, checker, mock_agent):
        # Arrange
        mock_agent.get_memory.return_value = {
            "court_availability": [
                {
                    "court": "Buena Vista",
                    "date": "2025-06-03",  # A Tuesday
                    "time": "18:00",
                    "available": True,
                }
            ]
        }

        # Act
        result = await checker.get_available_courts()

        # Assert
        assert len(result) == 1
        assert result[0]["court"] == "Buena Vista"
        assert result[0]["date"] == "2025-06-03"
        assert result[0]["time"] == "18:00"

    def test_filter_by_days_and_times(self, checker):
        # Arrange
        availabilities = [
            {
                "court": "Court A",
                "date": "2025-06-03",
                "time": "18:00",
                "available": True,
            },  # Tuesday 6pm
            {
                "court": "Court B",
                "date": "2025-06-03",
                "time": "19:00",
                "available": True,
            },  # Tuesday 7pm
            {
                "court": "Court C",
                "date": "2025-06-03",
                "time": "20:00",
                "available": True,
            },  # Tuesday 8pm
            {
                "court": "Court D",
                "date": "2025-06-04",
                "time": "18:00",
                "available": True,
            },  # Wednesday 6pm
            {
                "court": "Court E",
                "date": "2025-06-05",
                "time": "18:00",
                "available": True,
            },  # Thursday 6pm
            {
                "court": "Court F",
                "date": "2025-06-07",
                "time": "18:00",
                "available": True,
            },  # Saturday 6pm
        ]

        # Act
        result = checker.filter_by_days_and_times(
            availabilities,
            days=["Tuesday", "Thursday", "Saturday", "Sunday"],
            times=["18:00", "19:00"],
        )

        # Assert
        assert len(result) == 4
        courts = [item["court"] for item in result]
        assert "Court A" in courts  # Tuesday 6pm
        assert "Court B" in courts  # Tuesday 7pm
        assert "Court E" in courts  # Thursday 6pm
        assert "Court F" in courts  # Saturday 6pm
        assert "Court C" not in courts  # Tuesday 8pm (outside time range)
        assert "Court D" not in courts  # Wednesday (outside day range)


class TestCourtFactory:
    def test_create_all_courts(self):
        # Act
        courts = CourtFactory.create_all_courts()

        # Assert
        assert len(courts) > 0
        # Check that all courts have a name and URL
        for court in courts:
            assert court.name
            assert court.url
            assert isinstance(court, Court)

    def test_create_court(self):
        # Act
        court = CourtFactory.create_court("Test Court", "https://example.com")

        # Assert
        assert court.name == "Test Court"
        assert court.url == "https://example.com"
        assert isinstance(court, Court)
