"""SQLAlchemy models for PostgreSQL database."""

from datetime import datetime
from typing import Optional

from sqlalchemy import BIGINT, TIMESTAMP, VARCHAR, Index, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    """Base class for all models."""

    pass


class Player(Base):
    """Model for confirmed players."""

    __tablename__ = "players"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BIGINT, unique=True, nullable=False, index=True)
    username: Mapped[str] = mapped_column(VARCHAR(255), nullable=False, index=True)
    nickname: Mapped[str] = mapped_column(VARCHAR(100), nullable=False)
    screenshot_path: Mapped[Optional[str]] = mapped_column(VARCHAR(500), nullable=True)
    registration_date: Mapped[datetime] = mapped_column(
        TIMESTAMP, server_default=func.current_timestamp(), nullable=False
    )
    status: Mapped[str] = mapped_column(VARCHAR(50), default="Активен", nullable=False, index=True)
    added_by: Mapped[str] = mapped_column(VARCHAR(255), default="bot", nullable=False)
    exclusion_date: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP, nullable=True)
    exclusion_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    excluded_by: Mapped[Optional[str]] = mapped_column(VARCHAR(255), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, server_default=func.current_timestamp(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
        nullable=False,
    )

    __table_args__ = (
        Index("idx_players_telegram_id", "telegram_id"),
        Index("idx_players_username", "username"),
        Index("idx_players_status", "status"),
    )

    def __repr__(self) -> str:
        return f"<Player(id={self.id}, telegram_id={self.telegram_id}, username={self.username}, status={self.status})>"


class PendingRegistration(Base):
    """Model for pending registration requests."""

    __tablename__ = "pending_registrations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BIGINT, unique=True, nullable=False, index=True)
    username: Mapped[str] = mapped_column(VARCHAR(255), nullable=False, index=True)
    nickname: Mapped[str] = mapped_column(VARCHAR(100), nullable=False)
    screenshot_path: Mapped[str] = mapped_column(VARCHAR(500), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, server_default=func.current_timestamp(), nullable=False
    )

    __table_args__ = (
        Index("idx_pending_telegram_id", "telegram_id"),
        Index("idx_pending_username", "username"),
    )

    def __repr__(self) -> str:
        return f"<PendingRegistration(id={self.id}, telegram_id={self.telegram_id}, username={self.username})>"
