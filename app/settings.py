import os
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ENV: str = os.environ["STAGE"]

    DB_URI: str
    ECHO_SQL: bool
    REDIS_URI: str
    THROTTLING: bool
    REQUEST_TIMEOUT: int
    REGION: str

    model_config = SettingsConfigDict(
        env_file=Path(__file__).parent / f"config/{os.environ['APP_CONFIG_FILE']}.env",
        case_sensitive=True,
    )


settings = Settings.model_validate({})
