import json
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class GoogleSheetsConfig(BaseModel):
    """Google Sheets API configuration."""

    credentials_json: Optional[str] = Field(
        default=None,
        description="Path to credentials.json file"
    )
    credentials: Optional[str] = Field(
        default=None,
        description="Google credentials as JSON string (Railway)"
    )
    spreadsheet_id: str = Field(..., description="Google Sheets spreadsheet ID")
    sheet_name: str = Field(default="Игроки")

    @field_validator('spreadsheet_id')
    @classmethod
    def validate_spreadsheet_id(cls, v: str) -> str:
        if not v or v == "your_spreadsheet_id_here":
            raise ValueError("SPREADSHEET_ID is not configured")
        return v

    def get_credentials_path(self, base_dir: Path) -> Optional[Path]:
        """Get path to credentials.json file."""
        if self.credentials:
            return None  # Will use credentials string

        if not self.credentials_json:
            return None

        creds_path = Path(self.credentials_json)
        if not creds_path.is_absolute():
            creds_path = base_dir / creds_path

        return creds_path if creds_path.exists() else None

    def get_credentials_dict(self, base_dir: Path) -> Optional[dict]:
        """
        Get credentials as dictionary.

        Supports:
        1. GOOGLE_CREDENTIALS env var (Railway)
        2. credentials.json file (local)
        """
        # From environment variable
        if self.credentials:
            try:
                return json.loads(self.credentials)
            except json.JSONDecodeError:
                raise ValueError("GOOGLE_CREDENTIALS contains invalid JSON")

        # From file
        creds_path = self.get_credentials_path(base_dir)
        if creds_path and creds_path.exists():
            with open(creds_path, 'r') as f:
                return json.load(f)

        return None
