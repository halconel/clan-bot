import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator

from config.database import DatabaseConfig
from config.storage import StorageConfig

# Load environment variables
load_dotenv()

# Project root directory
BASE_DIR = Path(__file__).resolve().parent.parent


class TelegramConfig(BaseModel):
    """Telegram Bot configuration."""

    bot_token: str = Field(..., description="Telegram Bot API token")
    leader_telegram_id: int = Field(..., description="Telegram ID of clan leader")

    @field_validator("bot_token")
    @classmethod
    def validate_bot_token(cls, v: str) -> str:
        if not v or v == "YOUR_BOT_TOKEN_HERE":
            raise ValueError("BOT_TOKEN is not configured")
        if ":" not in v:
            raise ValueError("BOT_TOKEN has invalid format")
        return v

    @field_validator("leader_telegram_id")
    @classmethod
    def validate_leader_id(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("LEADER_TELEGRAM_ID must be positive")
        return v


class LoggingConfig(BaseModel):
    """Logging configuration."""

    log_level: str = Field(default="INFO")
    log_file: str = Field(default="bot.log")


class Settings(BaseModel):
    """Main application settings."""

    telegram: TelegramConfig
    database: DatabaseConfig
    storage: StorageConfig
    logging: LoggingConfig

    def ensure_directories(self):
        """Create necessary directories."""
        self.storage.ensure_directories(BASE_DIR)

    class Config:
        arbitrary_types_allowed = True


def load_settings() -> Settings:
    """Load and validate settings from environment."""
    try:
        settings = Settings(
            telegram=TelegramConfig(
                bot_token=os.getenv("BOT_TOKEN", ""),
                leader_telegram_id=int(os.getenv("LEADER_TELEGRAM_ID", "0")),
            ),
            database=DatabaseConfig(
                database_url=os.getenv("DATABASE_URL", ""),
            ),
            storage=StorageConfig(
                screenshots_dir=os.getenv("SCREENSHOTS_DIR", "data/screenshots"),
                temp_storage_file=os.getenv("TEMP_STORAGE_FILE", "data/pending.json"),
            ),
            logging=LoggingConfig(
                log_level=os.getenv("LOG_LEVEL", "INFO"),
                log_file=os.getenv("LOG_FILE", "bot.log"),
            ),
        )

        settings.ensure_directories()
        return settings

    except ValueError as e:
        raise ValueError(f"Configuration error: {e}") from e
