from pathlib import Path
from pydantic import BaseModel, Field


class StorageConfig(BaseModel):
    """Storage configuration for files and data."""

    screenshots_dir: str = Field(default="data/screenshots")
    temp_storage_file: str = Field(default="data/pending.json")

    def get_screenshots_path(self, base_dir: Path) -> Path:
        """Get absolute path to screenshots directory."""
        path = Path(self.screenshots_dir)
        if not path.is_absolute():
            path = base_dir / path
        return path

    def get_temp_storage_path(self, base_dir: Path) -> Path:
        """Get absolute path to temp storage file."""
        path = Path(self.temp_storage_file)
        if not path.is_absolute():
            path = base_dir / path
        return path

    def ensure_directories(self, base_dir: Path):
        """Create necessary directories if they don't exist."""
        screenshots_path = self.get_screenshots_path(base_dir)
        screenshots_path.mkdir(parents=True, exist_ok=True)

        storage_path = self.get_temp_storage_path(base_dir)
        storage_path.parent.mkdir(parents=True, exist_ok=True)
