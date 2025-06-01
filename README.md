# Pickleball Court Availability Checker

This project helps find available pickleball courts in San Francisco on specific days and times, then sends notifications to Slack.

## Features

- Checks availability for pickleball courts in San Francisco
- Focuses on Tuesdays, Thursdays, and weekends from 6pm to 8pm
- Sends availability notifications to Slack

## Requirements

- Python 3.12
- Playwright (Chromium)
- Slack API token

## Installation

1. Clone this repository
2. Install dependencies with Poetry:
   ```
   poetry install
   ```
3. Install Playwright:
   ```
   poetry run playwright install chromium --with-deps --no-shell
   ```

## Configuration

Create a `.env` file in the project root with the following variables:
```
OPENAI_API_KEY=your_openai_api_key
SLACK_API_TOKEN=your_slack_api_token
SLACK_CHANNEL=your_slack_channel_id
```

## Usage

Run the main script:
```
poetry run python main.py
```

## Development

This project follows:
- Python 3.12
- Ruff for linting and formatting
- Factory pattern for object creation
- Test-driven development

## Testing

Run tests:
```
poetry run pytest
```
