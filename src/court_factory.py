from dataclasses import dataclass
from typing import List


@dataclass
class Court:
    """Represents a pickleball court with a name and reservation URL."""

    name: str
    url: str


class CourtFactory:
    """Factory for creating Court objects."""

    @staticmethod
    def create_court(name: str, url: str) -> Court:
        """Create a single Court object.

        Args:
            name: The name of the court
            url: The URL for reservations

        Returns:
            A Court object
        """
        return Court(name=name, url=url)

    @staticmethod
    def create_all_courts() -> List[Court]:
        """Create all available pickleball courts in San Francisco.

        Returns:
            A list of Court objects
        """
        courts = [
            CourtFactory.create_court("Buena Vista", "https://www.rec.us/buenavista"),
            CourtFactory.create_court(
                "Goldman Tennis Center", "https://gtc.clubautomation.com/"
            ),
            CourtFactory.create_court("Jackson", "https://www.rec.us/jackson"),
            CourtFactory.create_court("Moscone", "https://rec.us/moscone"),
            CourtFactory.create_court("Parkside Square", "https://www.rec.us/parkside"),
            CourtFactory.create_court(
                "Presidio Wall", "https://www.rec.us/presidiowall"
            ),
            CourtFactory.create_court("Richmond", "https://www.rec.us/richmond"),
            CourtFactory.create_court("Rossi", "https://rec.us/rossi"),
            CourtFactory.create_court("Stern Grove", "https://rec.us/sterngrove"),
            CourtFactory.create_court("Upper Noe", "https://www.rec.us/uppernoe"),
        ]
        return courts
