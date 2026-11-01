"""Settings every Python service shares, read from environment variables.

Services subclass `CommonSettings` and add their own fields (database URL, peer URLs, ...).
Values come from the process environment only; Docker Compose supplies them.
"""

from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

LangStrategy = Literal["translate", "native", "hybrid"]
Environment = Literal["dev", "test", "ci", "prod"]


class CommonSettings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    service_name: str = "voiceserve"
    environment: Environment = "dev"
    log_level: str = "INFO"
    replay_mode: bool = False
    lang_strategy: LangStrategy = "hybrid"
    daily_budget_usd: float = Field(default=5.0, ge=0)
