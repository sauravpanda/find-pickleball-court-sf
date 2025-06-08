import os
from typing import Any, Dict, List

import requests

from .config import settings
from .exceptions import SlackNotificationError
from .logger import logger


class SlackNotifier:
    """Sends notifications to Slack about pickleball court availability."""

    def __init__(self):
        """Initialize the Slack notifier with webhook URL from environment variables."""
        self.webhook_url = settings.slack_webhook_url
        if not self.webhook_url:
            raise SlackNotificationError("SLACK_WEBHOOK_URL environment variable is required")
        logger.info("Initialized SlackNotifier")

    def send_notification(self, availabilities: List[Dict[str, Any]]) -> bool:
        """Send a notification to Slack with court availabilities.

        Args:
            availabilities: List of available court slots with court name, date, and time

        Returns:
            True if notification was sent successfully, False otherwise
        """
        message = self.format_message(availabilities)

        try:
            logger.info("Sending notification to Slack")
            response = requests.post(
                self.webhook_url, 
                json={"text": message},
                timeout=30
            )
            response.raise_for_status()
            logger.info("Notification sent successfully")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Error sending message to Slack: {e}")
            raise SlackNotificationError(f"Failed to send Slack notification: {e}") from e

    def format_message(self, availabilities: List[Dict[str, Any]]) -> str:
        """Format court availabilities into a readable message.

        Args:
            availabilities: List of available court slots with court name, date, and time

        Returns:
            Formatted message string
        """
        if not availabilities:
            return "No available pickleball courts found for your requested times."

        # Check if the availabilities contain actual data or just placeholder data
        # If all times for a court on a date are identical, it's likely placeholder data
        has_real_data = False
        date_court_times = {}
        
        for avail in availabilities:
            date = avail["date"]
            court = avail["court"]
            time = avail["time"]
            
            key = (date, court)
            if key not in date_court_times:
                date_court_times[key] = set()
            
            date_court_times[key].add(time)
        
        # Check if we have any court with varied times (real data)
        for times in date_court_times.values():
            if len(times) > 1 and not all(t == list(times)[0] for t in times):
                has_real_data = True
                break
        
        if not has_real_data:
            return "No available pickleball courts found for your requested times."

        message = "🏓 *Available Pickleball Courts* 🏓\n\n"

        # Group by date
        date_groups = {}
        for avail in availabilities:
            date = avail["date"]
            if date not in date_groups:
                date_groups[date] = []
            date_groups[date].append(avail)

        # Sort dates chronologically
        sorted_dates = sorted(date_groups.keys())

        # Format each date group
        for date in sorted_dates:
            courts = date_groups[date]
            # Convert date to more readable format (e.g., "Tuesday, June 3, 2025")
            try:
                import datetime

                date_obj = datetime.datetime.strptime(date, "%Y-%m-%d")
                formatted_date = date_obj.strftime("%A, %B %d, %Y")
            except ValueError:
                formatted_date = date

            message += f"*{formatted_date}*\n"

            # Group by court
            court_groups = {}
            for court in courts:
                court_name = court["court"]
                if court_name not in court_groups:
                    court_groups[court_name] = []
                court_groups[court_name].append(court)

            # Sort courts alphabetically for consistent output
            sorted_courts = sorted(court_groups.keys())

            # Format each court group
            for court_name in sorted_courts:
                times = court_groups[court_name]
                # Extract unique times and convert to 12-hour format
                time_slots = {}  # Use a dict to track time slots
                
                for t in times:
                    try:
                        time_obj = datetime.datetime.strptime(t["time"], "%H:%M")
                        hour_key = time_obj.hour  # Group by hour
                        
                        if hour_key not in time_slots:
                            time_slots[hour_key] = []
                        
                        formatted_time = time_obj.strftime("%-I:%M %p")
                        time_slots[hour_key].append(formatted_time)
                    except ValueError:
                        # Handle non-standard time formats
                        if t["time"] not in time_slots:
                            time_slots[t["time"]] = [t["time"]]
                
                if time_slots:
                    # Sort hours for consistent output
                    sorted_hours = sorted(time_slots.keys())
                    
                    # Format the time slots in a readable way
                    time_parts = []
                    for hour in sorted_hours:
                        slots = sorted(set(time_slots[hour]))  # Remove duplicates
                        if isinstance(hour, int):
                            # For standard hour-based slots
                            if len(slots) == 1:
                                time_parts.append(slots[0])
                            else:
                                # Group multiple slots in the same hour
                                hour_ampm = "AM" if hour < 12 else "PM"
                                display_hour = hour if hour <= 12 else hour - 12
                                display_hour = 12 if display_hour == 0 else display_hour
                                minutes = [s.split(":")[1].split(" ")[0] for s in slots]
                                time_parts.append(f"{display_hour}:{', '.join(minutes)} {hour_ampm}")
                        else:
                            # For non-standard formats
                            time_parts.append(", ".join(slots))
                    
                    time_str = " | ".join(time_parts)
                    message += f"• {court_name}: {time_str}\n"

            message += "\n"

        message += (
            "Book your court at https://sfrecpark.org/1591/Reservable-Pickleball-Courts"
        )

        return message
