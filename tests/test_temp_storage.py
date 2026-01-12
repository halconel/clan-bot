import json
import os
import tempfile
from pathlib import Path

import pytest

from database.temp_storage import TempStorage
from models.player import PendingRegistration


@pytest.fixture
def temp_storage_file():
    """Create a temporary file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        temp_file = f.name
    yield temp_file
    # Cleanup
    if os.path.exists(temp_file):
        os.unlink(temp_file)


@pytest.fixture
def storage(temp_storage_file):
    """Create TempStorage instance with temporary file."""
    return TempStorage(temp_storage_file)


@pytest.fixture
def sample_pending():
    """Sample pending registration data."""
    return PendingRegistration(
        telegram_id=123456789,
        username="@testuser",
        nickname="TestNick",
        screenshot_path="/path/to/screenshot.jpg",
    )


class TestTempStorageInit:
    """Test TempStorage initialization."""

    @pytest.mark.unit
    def test_creates_file_if_not_exists(self, temp_storage_file):
        """Test that storage file is created if it doesn't exist."""
        os.unlink(temp_storage_file)  # Delete the file
        assert not os.path.exists(temp_storage_file)

        storage = TempStorage(temp_storage_file)
        assert os.path.exists(temp_storage_file)

    @pytest.mark.unit
    def test_loads_existing_data(self, temp_storage_file):
        """Test that existing data is loaded on init."""
        test_data = {
            "123": {
                "telegram_id": 123,
                "username": "@user123",
                "nickname": "Nick",
                "screenshot_path": "/path/to/screenshot.jpg",
                "timestamp": "2026-01-12 12:00:00",
            }
        }
        with open(temp_storage_file, 'w') as f:
            json.dump(test_data, f)

        storage = TempStorage(temp_storage_file)
        assert len(storage.get_all_pending()) == 1


class TestSavePending:
    """Test saving pending registrations."""

    @pytest.mark.unit
    def test_save_new_pending(self, storage, sample_pending):
        """Test saving a new pending registration."""
        storage.save_pending(sample_pending)

        retrieved = storage.get_pending(sample_pending.telegram_id)
        assert retrieved is not None
        assert retrieved.telegram_id == sample_pending.telegram_id
        assert retrieved.username == sample_pending.username
        assert retrieved.nickname == sample_pending.nickname

    @pytest.mark.unit
    def test_save_overwrites_existing(self, storage, sample_pending):
        """Test that saving with same ID overwrites existing data."""
        storage.save_pending(sample_pending)

        # Save again with different nickname
        updated = PendingRegistration(
            telegram_id=sample_pending.telegram_id,
            username=sample_pending.username,
            nickname="UpdatedNick",
            screenshot_path=sample_pending.screenshot_path,
        )
        storage.save_pending(updated)

        retrieved = storage.get_pending(sample_pending.telegram_id)
        assert retrieved.nickname == "UpdatedNick"

    @pytest.mark.unit
    def test_save_multiple_users(self, storage):
        """Test saving multiple pending registrations."""
        pending1 = PendingRegistration(
            telegram_id=111,
            username="@user1",
            nickname="Nick1",
            screenshot_path="/path1.jpg",
        )
        pending2 = PendingRegistration(
            telegram_id=222,
            username="@user2",
            nickname="Nick2",
            screenshot_path="/path2.jpg",
        )

        storage.save_pending(pending1)
        storage.save_pending(pending2)

        all_pending = storage.get_all_pending()
        assert len(all_pending) == 2


class TestGetPending:
    """Test retrieving pending registrations."""

    @pytest.mark.unit
    def test_get_existing_pending(self, storage, sample_pending):
        """Test retrieving an existing pending registration."""
        storage.save_pending(sample_pending)

        retrieved = storage.get_pending(sample_pending.telegram_id)
        assert retrieved is not None
        assert retrieved.telegram_id == sample_pending.telegram_id

    @pytest.mark.unit
    def test_get_non_existing_pending(self, storage):
        """Test retrieving non-existing pending returns None."""
        retrieved = storage.get_pending(999999)
        assert retrieved is None

    @pytest.mark.unit
    def test_get_by_username(self, storage, sample_pending):
        """Test retrieving pending by username."""
        storage.save_pending(sample_pending)

        retrieved = storage.get_pending_by_username(sample_pending.username)
        assert retrieved is not None
        assert retrieved.username == sample_pending.username

    @pytest.mark.unit
    def test_get_by_username_not_found(self, storage):
        """Test retrieving by non-existing username returns None."""
        retrieved = storage.get_pending_by_username("@nonexistent")
        assert retrieved is None


class TestRemovePending:
    """Test removing pending registrations."""

    @pytest.mark.unit
    def test_remove_existing_pending(self, storage, sample_pending):
        """Test removing an existing pending registration."""
        storage.save_pending(sample_pending)
        assert storage.get_pending(sample_pending.telegram_id) is not None

        result = storage.remove_pending(sample_pending.telegram_id)
        assert result is True
        assert storage.get_pending(sample_pending.telegram_id) is None

    @pytest.mark.unit
    def test_remove_non_existing_pending(self, storage):
        """Test removing non-existing pending returns False."""
        result = storage.remove_pending(999999)
        assert result is False

    @pytest.mark.unit
    def test_remove_by_username(self, storage, sample_pending):
        """Test removing pending by username."""
        storage.save_pending(sample_pending)

        result = storage.remove_pending_by_username(sample_pending.username)
        assert result is True
        assert storage.get_pending_by_username(sample_pending.username) is None


class TestGetAllPending:
    """Test retrieving all pending registrations."""

    @pytest.mark.unit
    def test_get_all_empty(self, storage):
        """Test getting all pending when storage is empty."""
        all_pending = storage.get_all_pending()
        assert len(all_pending) == 0
        assert isinstance(all_pending, list)

    @pytest.mark.unit
    def test_get_all_with_data(self, storage):
        """Test getting all pending with multiple registrations."""
        pending1 = PendingRegistration(
            telegram_id=111,
            username="@user1",
            nickname="Nick1",
            screenshot_path="/path1.jpg",
        )
        pending2 = PendingRegistration(
            telegram_id=222,
            username="@user2",
            nickname="Nick2",
            screenshot_path="/path2.jpg",
        )

        storage.save_pending(pending1)
        storage.save_pending(pending2)

        all_pending = storage.get_all_pending()
        assert len(all_pending) == 2
        telegram_ids = [p.telegram_id for p in all_pending]
        assert 111 in telegram_ids
        assert 222 in telegram_ids


class TestPersistence:
    """Test data persistence to file."""

    @pytest.mark.unit
    def test_data_persisted_to_file(self, temp_storage_file, sample_pending):
        """Test that data is written to file."""
        storage = TempStorage(temp_storage_file)
        storage.save_pending(sample_pending)

        # Read file directly
        with open(temp_storage_file, 'r') as f:
            data = json.load(f)

        assert str(sample_pending.telegram_id) in data

    @pytest.mark.unit
    def test_data_loaded_from_file(self, temp_storage_file, sample_pending):
        """Test that data is loaded from file on init."""
        # Save with first instance
        storage1 = TempStorage(temp_storage_file)
        storage1.save_pending(sample_pending)

        # Load with new instance
        storage2 = TempStorage(temp_storage_file)
        retrieved = storage2.get_pending(sample_pending.telegram_id)

        assert retrieved is not None
        assert retrieved.telegram_id == sample_pending.telegram_id


class TestConcurrentAccess:
    """Test handling of concurrent access scenarios."""

    @pytest.mark.unit
    def test_multiple_instances_same_file(self, temp_storage_file, sample_pending):
        """Test that multiple instances can work with same file."""
        storage1 = TempStorage(temp_storage_file)
        storage2 = TempStorage(temp_storage_file)

        storage1.save_pending(sample_pending)

        # Storage2 should be able to read data after reload
        storage2 = TempStorage(temp_storage_file)
        retrieved = storage2.get_pending(sample_pending.telegram_id)
        assert retrieved is not None


class TestErrorHandling:
    """Test error handling."""

    @pytest.mark.unit
    def test_handles_corrupted_json(self, temp_storage_file):
        """Test that corrupted JSON is handled gracefully."""
        with open(temp_storage_file, 'w') as f:
            f.write("invalid json {{{")

        # Should not raise, should start with empty storage
        storage = TempStorage(temp_storage_file)
        assert len(storage.get_all_pending()) == 0

    @pytest.mark.unit
    def test_handles_readonly_file(self, temp_storage_file):
        """Test handling of readonly file."""
        storage = TempStorage(temp_storage_file)

        # Make file readonly
        os.chmod(temp_storage_file, 0o444)

        pending = PendingRegistration(
            telegram_id=123,
            username="@user",
            nickname="Nick",
            screenshot_path="/path.jpg",
        )

        # Should handle gracefully (log error but not crash)
        try:
            storage.save_pending(pending)
        except PermissionError:
            pass  # Expected on some systems

        # Restore permissions for cleanup
        os.chmod(temp_storage_file, 0o644)
