"""Configuration settings for the Pickleball Court Availability Checker."""

import os
from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # OpenAI Configuration
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    
    # Slack Configuration
    slack_webhook_url: str = Field(..., env="SLACK_WEBHOOK_URL")
    slack_api_token: Optional[str] = Field(None, env="SLACK_API_TOKEN")
    slack_channel: Optional[str] = Field(None, env="SLACK_CHANNEL")
    
    # Court Checking Configuration
    default_days: List[str] = Field(
        default=["Tuesday", "Thursday", "Saturday", "Sunday"],
        description="Default days to check for court availability"
    )
    default_times: List[str] = Field(
        default=["18:00", "19:00"],
        description="Default times to check for court availability"
    )
    
    # Browser Configuration
    browser_headless: bool = Field(default=True, env="BROWSER_HEADLESS")
    browser_timeout: int = Field(default=30, env="BROWSER_TIMEOUT")
    
    # Rate Limiting
    request_delay: float = Field(default=2.0, env="REQUEST_DELAY", description="Delay between court checks in seconds")
    max_retries: int = Field(default=3, env="MAX_RETRIES")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings() 