import asyncio
import datetime
from typing import Any, Dict, List, Optional

from browser_use import Agent
from browser_use.browser import BrowserProfile
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from .config import settings
from .court_factory import Court
from .exceptions import BrowserError, CourtCheckError
from .logger import logger


class CourtAvailability(BaseModel):
    """Model for court availability data."""
    
    court: str
    date: str
    time: str
    available: bool = True


class CourtAvailabilities(BaseModel):
    """Model for a list of court availabilities."""
    
    availabilities: List[CourtAvailability] = Field(default_factory=list)


class CourtAvailabilityChecker:
    """Checks pickleball court availability using browser-use."""

    def __init__(self, agent: Optional[Agent] = None, browser_headless: bool = False):
        """Initialize the court availability checker.

        Args:
            agent: Optional pre-configured browser-use Agent
        """
        self.agent = agent
        self.browser_profile = BrowserProfile(
            window_size={"width": 1920, "height": 1080},
            headless=browser_headless,
        )
        self.availabilities: List[CourtAvailability] = []
        self.all_court_data: Dict[str, List[CourtAvailability]] = {}
        logger.info("Initialized CourtAvailabilityChecker")

    async def check_availability(
        self, court: Court, days: List[str], times: List[str]
    ) -> None:
        """Check availability for a specific court on given days and times.

        Args:
            court: The Court object to check
            days: List of days to check (e.g., ["Tuesday", "Thursday"])
            times: List of times to check (e.g., ["18:00", "19:00"])
            
        Raises:
            CourtCheckError: If unable to check availability after retries
        """
        for attempt in range(settings.max_retries):
            try:
                await self._check_availability_once(court, days, times)
                return  # Success, exit retry loop
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1}/{settings.max_retries} failed for {court.name}: {e}")
                if attempt == settings.max_retries - 1:
                    raise CourtCheckError(f"Failed to check {court.name} after {settings.max_retries} attempts") from e
                await asyncio.sleep(1)  # Wait before retry

    async def _check_availability_once(
        self, court: Court, days: List[str], times: List[str]
    ) -> None:
        """Single attempt to check availability for a court."""
        # Create a detailed task description for the agent
        task = (
            f"Check availability for {court.name} pickleball court on {', '.join(days)} "
            f"at times {', '.join(times)}.\n\n"
            f"1. Navigate to {court.url}\n"
            f"2. Find the reservation system or calendar\n"
            f"3. Look for available slots on {', '.join(days)} between {' and '.join(times)}\n"
            f"4. IMPORTANT: Only return slots that are ACTUALLY AVAILABLE for booking. Do not return placeholder data.\n"
            f"5. If you cannot determine the actual availability, return an empty array.\n"
            f"6. Return the results in the following JSON format:\n"
            f"{{\n"
            f'  "availabilities": [\n'
            f'    {{\n'
            f'      "court": "{court.name}",\n'
            f'      "date": "YYYY-MM-DD",\n'
            f'      "time": "HH:MM",\n'
            f'      "available": true\n'
            f'    }}\n'
            f'  ]\n'
            f"}}\n"
            f"7. If no slots are available, return: {{ \"availabilities\": [] }}\n"
            f"8. Do not include duplicate times or placeholder data in your response.\n"
            f"9. Only include times that are actually available for booking."
        )

        # Create a new agent for each court check
        agent = Agent(
            task=task,
            llm=ChatOpenAI(model="gpt-4o"),
            browser_profile=self.browser_profile,
        )

        # Run the agent and get the history
        try:
            history = await agent.run()
            
            # Extract the final result from history
            result = history.final_result()
            if result:
                try:
                    # Check if the result is valid JSON
                    if result.strip().startswith("{"):
                        # Parse the JSON result
                        parsed = CourtAvailabilities.model_validate_json(result)
                        
                        # Store the court data separately
                        self.all_court_data[court.name] = parsed.availabilities
                        
                        # Add the availabilities to our list
                        self.availabilities.extend(parsed.availabilities)
                        
                        logger.info(f"Found {len(parsed.availabilities)} available slots for {court.name}")
                    else:
                        # Handle text responses by creating an empty availabilities object
                        logger.info(f"No JSON data returned for {court.name}. Text response: {result[:100]}...")
                        logger.info(f"Found 0 available slots for {court.name}")
                except Exception as e:
                    logger.error(f"Error parsing result for {court.name}: {e}")
                    logger.debug(f"Raw result: {result}")
                    logger.info(f"Found 0 available slots for {court.name}")
            else:
                logger.info(f"No availability data returned for {court.name}")
                logger.info(f"Found 0 available slots for {court.name}")
        except Exception as e:
            logger.error(f"Error checking availability for {court.name}: {e}")
            raise BrowserError(f"Browser error for {court.name}: {e}") from e

    async def get_available_courts(
        self, days: Optional[List[str]] = None, times: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Get all available courts based on collected availability data.
        
        Args:
            days: Optional list of days to filter by (e.g., ["Tuesday", "Thursday"])
            times: Optional list of times to filter by (e.g., ["18:00", "19:00"])
            
        Returns:
            List of availability dictionaries
        """
        # Convert the CourtAvailability objects to dictionaries
        availabilities = [avail.model_dump() for avail in self.availabilities]
        
        # Filter by days and times if provided
        if days or times:
            availabilities = self.filter_by_days_and_times(availabilities, days, times)

        return availabilities

    def filter_by_days_and_times(
        self,
        availabilities: List[Dict[str, Any]],
        days: Optional[List[str]] = None,
        times: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Filter availabilities by specific days and times.

        Args:
            availabilities: List of availability dictionaries
            days: Optional list of days to filter by (e.g., ["Tuesday", "Thursday"])
            times: Optional list of times to filter by (e.g., ["18:00", "19:00"])

        Returns:
            Filtered list of availabilities
        """
        filtered = availabilities.copy()

        if days:
            filtered = [
                avail
                for avail in filtered
                if self._get_day_of_week_safe(avail["date"]) in days
            ]

        if times:
            # Interpret times as a range if they are in sequence
            time_ranges = self._extract_time_ranges(times)
            
            # Filter by time ranges
            filtered = [
                avail
                for avail in filtered
                if self._is_time_in_ranges(avail["time"], time_ranges)
            ]

        return filtered
    
    def _extract_time_ranges(self, times: List[str]) -> List[tuple]:
        """Extract time ranges from a list of times.
        
        Args:
            times: List of times in HH:MM format
            
        Returns:
            List of (start_time, end_time) tuples in minutes since midnight
        """
        # Convert times to minutes since midnight for easier comparison
        minutes = []
        for t in times:
            try:
                hours, mins = map(int, t.split(':'))
                minutes.append(hours * 60 + mins)
            except (ValueError, IndexError):
                continue
                
        # Sort minutes
        minutes.sort()
        
        # Find continuous ranges
        ranges = []
        start = None
        prev = None
        
        for m in minutes:
            if start is None:
                start = m
                prev = m
            elif m - prev > 60:  # If more than 1 hour gap, start a new range
                ranges.append((start, prev))
                start = m
                prev = m
            else:
                prev = m
                
        # Add the last range
        if start is not None:
            ranges.append((start, prev))
            
        return ranges
    
    def _is_time_in_ranges(self, time_str: str, time_ranges: List[tuple]) -> bool:
        """Check if a time is within any of the specified ranges.
        
        Args:
            time_str: Time string in HH:MM format
            time_ranges: List of (start_time, end_time) tuples in minutes since midnight
            
        Returns:
            True if the time is within any range, False otherwise
        """
        try:
            hours, mins = map(int, time_str.split(':'))
            minutes = hours * 60 + mins
            
            for start, end in time_ranges:
                if start <= minutes <= end:
                    return True
            
            return False
        except (ValueError, IndexError):
            # If we can't parse the time, assume it's not in range
            return False

    def _get_day_of_week_safe(self, date_str: str) -> str:
        """Convert a date string to day of week, safely handling invalid formats.

        Args:
            date_str: Date string in format YYYY-MM-DD

        Returns:
            Day of week (Monday, Tuesday, etc.) or the original string if parsing fails
        """
        try:
            date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d")
            return date_obj.strftime("%A")
        except ValueError:
            # If the date_str is already a day of the week, return it as is
            days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            if date_str in days_of_week:
                return date_str
            # Otherwise return an empty string to ensure it doesn't match any day filter
            return ""
