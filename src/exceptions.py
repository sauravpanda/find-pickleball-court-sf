"""Custom exceptions for the Pickleball Court Availability Checker."""


class PickleballCheckerError(Exception):
    """Base exception for pickleball checker errors."""
    pass


class ConfigurationError(PickleballCheckerError):
    """Raised when there's a configuration issue."""
    pass


class CourtCheckError(PickleballCheckerError):
    """Raised when there's an error checking court availability."""
    pass


class SlackNotificationError(PickleballCheckerError):
    """Raised when there's an error sending Slack notifications."""
    pass


class BrowserError(PickleballCheckerError):
    """Raised when there's a browser-related error."""
    pass


class RateLimitError(PickleballCheckerError):
    """Raised when rate limits are exceeded."""
    pass 