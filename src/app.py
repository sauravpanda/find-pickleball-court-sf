import asyncio
from typing import List, Optional

from .config import settings
from .court_availability import CourtAvailabilityChecker
from .court_factory import CourtFactory
from .exceptions import ConfigurationError, CourtCheckError
from .logger import logger
from .slack_notifier import SlackNotifier


class PickleballCourtApp:
    """Main application for checking pickleball court availability and sending notifications."""

    def __init__(
        self,
        court_checker: Optional[CourtAvailabilityChecker] = None,
        slack_notifier: Optional[SlackNotifier] = None,
        days: Optional[List[str]] = None,
        times: Optional[List[str]] = None,
    ):
        """Initialize the pickleball court app.

        Args:
            court_checker: Optional pre-configured CourtAvailabilityChecker
            slack_notifier: Optional pre-configured SlackNotifier
            days: Optional list of days to check
            times: Optional list of times to check
        """
        try:
            self.court_checker = court_checker or CourtAvailabilityChecker()
            self.slack_notifier = slack_notifier or SlackNotifier()
            self.days = days or settings.default_days
            self.times = times or settings.default_times
            
            logger.info(f"Initialized app with days: {self.days}, times: {self.times}")
        except Exception as e:
            raise ConfigurationError(f"Failed to initialize application: {e}") from e

    async def run(self) -> None:
        """Run the application to check court availability and send notifications."""
        try:
            logger.info(
                f"Starting court availability check for {', '.join(self.days)} at {', '.join(self.times)}"
            )

            # Get all courts using the factory pattern
            courts = CourtFactory.create_all_courts()
            logger.info(f"Found {len(courts)} courts to check")

            # Check availability for each court with rate limiting
            successful_checks = 0
            failed_checks = 0
            
            for i, court in enumerate(courts):
                try:
                    logger.info(f"Checking {court.name} ({i+1}/{len(courts)})")
                    await self.court_checker.check_availability(court, self.days, self.times)
                    successful_checks += 1
                    
                    # Rate limiting - delay between requests
                    if i < len(courts) - 1:  # Don't delay after the last court
                        await asyncio.sleep(settings.request_delay)
                        
                except Exception as e:
                    logger.error(f"Failed to check {court.name}: {e}")
                    failed_checks += 1
                    continue

            logger.info(f"Court checks completed: {successful_checks} successful, {failed_checks} failed")

            # Get available courts filtered by days and times
            availabilities = await self.court_checker.get_available_courts(
                days=self.days, times=self.times
            )

            if availabilities:
                logger.info(f"Found {len(availabilities)} available slots")
            else:
                logger.info("No available slots found")

            # Send notification
            try:
                success = self.slack_notifier.send_notification(availabilities)
                if success:
                    logger.info("Notification sent successfully")
                else:
                    logger.error("Failed to send notification")
            except Exception as e:
                logger.error(f"Error sending notification: {e}")
                raise CourtCheckError(f"Failed to send notification: {e}") from e

            logger.info("Application run completed successfully")

        except Exception as e:
            logger.error(f"Application run failed: {e}")
            raise
