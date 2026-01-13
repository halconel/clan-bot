"""Database configuration."""

from pydantic import BaseModel, Field, field_validator


class DatabaseConfig(BaseModel):
    """PostgreSQL database configuration."""

    database_url: str = Field(..., description="PostgreSQL connection URL")

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Validate DATABASE_URL format."""
        if not v:
            raise ValueError("DATABASE_URL is not configured")

        # Allow SQLite for testing
        if v.startswith("sqlite"):
            return v

        if not v.startswith(("postgresql://", "postgresql+asyncpg://")):
            raise ValueError(
                "DATABASE_URL must start with 'postgresql://', 'postgresql+asyncpg://', or 'sqlite' (for testing)"
            )

        # Ensure asyncpg driver for async support
        if v.startswith("postgresql://") and "+asyncpg" not in v:
            v = v.replace("postgresql://", "postgresql+asyncpg://")

        return v

    class Config:
        arbitrary_types_allowed = True
