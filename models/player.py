from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Player:
    """Player data model for clan member."""

    telegram_id: int
    username: str
    nickname: str
    screenshot_path: Optional[str] = None
    registration_date: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))
    status: str = "Активен"
    added_by: str = "bot"
    notes: str = ""

    def to_dict(self) -> dict:
        """
        Convert Player instance to dictionary.

        Returns:
            Dictionary representation of player data
        """
        return {
            "telegram_id": self.telegram_id,
            "username": self.username,
            "nickname": self.nickname,
            "screenshot_path": self.screenshot_path,
            "registration_date": self.registration_date,
            "status": self.status,
            "added_by": self.added_by,
            "notes": self.notes,
        }

    def to_sheet_row(self) -> list:
        """
        Convert Player instance to Google Sheets row format.

        Returns:
            List of values in order matching sheet columns:
            [Telegram ID, Username, Nickname, Registration Date, Status, Added By, Notes]
        """
        return [
            str(self.telegram_id),
            self.username,
            self.nickname,
            self.registration_date,
            self.status,
            self.added_by,
            self.notes,
        ]

    @classmethod
    def from_dict(cls, data: dict) -> "Player":
        """
        Create Player instance from dictionary.

        Args:
            data: Dictionary with player data

        Returns:
            Player instance
        """
        return cls(
            telegram_id=int(data.get("telegram_id", 0)),
            username=data.get("username", ""),
            nickname=data.get("nickname", ""),
            screenshot_path=data.get("screenshot_path"),
            registration_date=data.get("registration_date", datetime.now().strftime("%Y-%m-%d")),
            status=data.get("status", "Активен"),
            added_by=data.get("added_by", "bot"),
            notes=data.get("notes", ""),
        )

    @classmethod
    def from_sheet_row(cls, row: list) -> "Player":
        """
        Create Player instance from Google Sheets row.

        Args:
            row: List of values from sheet row
                 [Telegram ID, Username, Nickname, Registration Date, Status, Added By, Notes]

        Returns:
            Player instance
        """
        return cls(
            telegram_id=int(row[0]) if row[0] else 0,
            username=row[1] if len(row) > 1 else "",
            nickname=row[2] if len(row) > 2 else "",
            registration_date=row[3] if len(row) > 3 else datetime.now().strftime("%Y-%m-%d"),
            status=row[4] if len(row) > 4 else "Активен",
            added_by=row[5] if len(row) > 5 else "bot",
            notes=row[6] if len(row) > 6 else "",
            screenshot_path=None,  # Screenshots not stored in Google Sheets
        )

    def __str__(self) -> str:
        """String representation of Player."""
        return f"Player({self.username} - {self.nickname})"

    def __repr__(self) -> str:
        """Developer-friendly representation of Player."""
        return (
            f"Player(telegram_id={self.telegram_id}, username='{self.username}', "
            f"nickname='{self.nickname}', status='{self.status}')"
        )


@dataclass
class PendingRegistration:
    """Temporary model for pending player registrations."""

    telegram_id: int
    username: str
    nickname: str
    screenshot_path: str
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON storage."""
        return {
            "telegram_id": self.telegram_id,
            "username": self.username,
            "nickname": self.nickname,
            "screenshot_path": self.screenshot_path,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PendingRegistration":
        """Create instance from dictionary."""
        return cls(
            telegram_id=int(data.get("telegram_id", 0)),
            username=data.get("username", ""),
            nickname=data.get("nickname", ""),
            screenshot_path=data.get("screenshot_path", ""),
            timestamp=data.get("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        )

    def to_player(self, added_by: str = "bot", notes: str = "via /accept") -> Player:
        """
        Convert pending registration to Player instance.

        Args:
            added_by: Who approved the registration
            notes: Additional notes

        Returns:
            Player instance
        """
        return Player(
            telegram_id=self.telegram_id,
            username=self.username,
            nickname=self.nickname,
            screenshot_path=self.screenshot_path,
            registration_date=datetime.now().strftime("%Y-%m-%d"),
            status="Активен",
            added_by=added_by,
            notes=notes,
        )

    def __str__(self) -> str:
        """String representation."""
        return f"PendingRegistration({self.username} - {self.nickname})"
