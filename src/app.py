from typing import List, Optional
from .court_availability import CourtAvailabilityChecker
from .slack_notifier import SlackNotifier
from .court_factory import CourtFactory


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
            days: Optional list of days to check (defaults to Tuesday, Thursday, Saturday, Sunday)
            times: Optional list of times to check (defaults to 18:00, 19:00)
        """
        self.court_checker = court_checker or CourtAvailabilityChecker()
        self.slack_notifier = slack_notifier or SlackNotifier()
        self.days = days or ["Tuesday", "Thursday", "Saturday", "Sunday"]
        self.times = times or ["18:00", "19:00"]

    async def run(self) -> None:
        """Run the application to check court availability and send notifications."""
        print(
            f"Checking pickleball court availability for {', '.join(self.days)} at {', '.join(self.times)}..."
        )

        # Get all courts using the factory pattern
        courts = CourtFactory.create_all_courts()

        # Check availability for each court and collect data
        print("Collecting court availability data...")
        for court in courts:
            print(f"Checking {court.name}...")
            await self.court_checker.check_availability(court, self.days, self.times)
            # No notification sent here - we'll collect all data first

        # Get available courts filtered by days and times
        availabilities = await self.court_checker.get_available_courts(
            days=self.days, times=self.times
        )

        # Send a single consolidated notification with all court data
        print(f"Sending consolidated notification with data from {len(courts)} courts...")
        success = self.slack_notifier.send_notification(availabilities)

        if success:
            print("Consolidated notification sent successfully!")
        else:
            print("Failed to send notification.")

        print("Done!")
