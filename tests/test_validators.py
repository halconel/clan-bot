import pytest
from utils.validators import (
    validate_nickname,
    validate_username,
    normalize_username,
    parse_add_command,
    parse_accept_command,
    sanitize_filename,
)


class TestValidateNickname:
    """Unit tests for nickname validation."""

    @pytest.mark.unit
    def test_valid_nicknames(self):
        """Test that valid nicknames pass validation."""
        valid_nicks = ["Player123", "Дракон", "Test_User", "Pro-Gamer", "А Б"]
        for nick in valid_nicks:
            is_valid, error = validate_nickname(nick)
            assert is_valid, f"{nick} should be valid, got error: {error}"
            assert error == ""

    @pytest.mark.unit
    def test_empty_nickname(self):
        """Test that empty nickname is invalid."""
        is_valid, error = validate_nickname("")
        assert not is_valid
        assert "пустым" in error.lower()

    @pytest.mark.unit
    def test_too_short_nickname(self):
        """Test that nickname shorter than 3 chars is invalid."""
        is_valid, error = validate_nickname("AB")
        assert not is_valid
        assert "короткий" in error.lower()

    @pytest.mark.unit
    def test_too_long_nickname(self):
        """Test that nickname longer than 20 chars is invalid."""
        is_valid, error = validate_nickname("A" * 21)
        assert not is_valid
        assert "длинный" in error.lower()

    @pytest.mark.unit
    def test_special_characters_in_nickname(self):
        """Test that special characters are not allowed."""
        invalid_nicks = ["Player@123", "Test#User", "Name!", "User$$$"]
        for nick in invalid_nicks:
            is_valid, error = validate_nickname(nick)
            assert not is_valid, f"{nick} should be invalid"

    @pytest.mark.unit
    def test_emoji_in_nickname(self):
        """Test that emojis are not allowed."""
        is_valid, error = validate_nickname("Player😀")
        assert not is_valid


class TestValidateUsername:
    """Unit tests for username validation."""

    @pytest.mark.unit
    def test_valid_usernames(self):
        """Test that valid usernames pass validation."""
        valid_users = ["@player123", "@TestUser", "@user_name", "player123"]
        for user in valid_users:
            is_valid, error = validate_username(user)
            assert is_valid, f"{user} should be valid, got error: {error}"
            assert error == ""

    @pytest.mark.unit
    def test_empty_username(self):
        """Test that empty username is invalid."""
        is_valid, error = validate_username("")
        assert not is_valid
        assert "пустым" in error.lower()

    @pytest.mark.unit
    def test_too_short_username(self):
        """Test that username shorter than 5 chars (+ @) is invalid."""
        is_valid, error = validate_username("@abc")
        assert not is_valid
        assert "короткий" in error.lower()

    @pytest.mark.unit
    def test_too_long_username(self):
        """Test that username longer than 32 chars (+ @) is invalid."""
        is_valid, error = validate_username("@" + "a" * 33)
        assert not is_valid
        assert "длинный" in error.lower()

    @pytest.mark.unit
    def test_special_characters_in_username(self):
        """Test that special characters are not allowed."""
        invalid_users = ["@user-name", "@user.name", "@user@name"]
        for user in invalid_users:
            is_valid, error = validate_username(user)
            assert not is_valid, f"{user} should be invalid"

    @pytest.mark.unit
    def test_username_without_at_symbol(self):
        """Test that username without @ is also accepted and validated."""
        is_valid, error = validate_username("player123")
        assert is_valid


class TestNormalizeUsername:
    """Unit tests for username normalization."""

    @pytest.mark.unit
    def test_adds_at_symbol_if_missing(self):
        """Test that @ is added if missing."""
        assert normalize_username("player123") == "@player123"

    @pytest.mark.unit
    def test_keeps_at_symbol_if_present(self):
        """Test that @ is not duplicated."""
        assert normalize_username("@player123") == "@player123"

    @pytest.mark.unit
    def test_strips_whitespace(self):
        """Test that whitespace is stripped."""
        assert normalize_username("  player123  ") == "@player123"
        assert normalize_username("  @player123  ") == "@player123"


class TestParseAddCommand:
    """Unit tests for /add command parsing."""

    @pytest.mark.unit
    def test_valid_add_command(self):
        """Test parsing of valid /add command."""
        is_valid, username, nickname, error = parse_add_command("/add @player123 DragonSlayer")
        assert is_valid
        assert username == "@player123"
        assert nickname == "DragonSlayer"
        assert error == ""

    @pytest.mark.unit
    def test_add_command_without_at_symbol(self):
        """Test that username without @ is normalized."""
        is_valid, username, nickname, error = parse_add_command("/add player123 DragonSlayer")
        assert is_valid
        assert username == "@player123"

    @pytest.mark.unit
    def test_add_command_missing_nickname(self):
        """Test that command with missing nickname is invalid."""
        is_valid, username, nickname, error = parse_add_command("/add @player123")
        assert not is_valid
        assert "формат" in error.lower()

    @pytest.mark.unit
    def test_add_command_invalid_username(self):
        """Test that command with invalid username is rejected."""
        is_valid, username, nickname, error = parse_add_command("/add @ab DragonSlayer")
        assert not is_valid
        assert "username" in error.lower()

    @pytest.mark.unit
    def test_add_command_invalid_nickname(self):
        """Test that command with invalid nickname is rejected."""
        is_valid, username, nickname, error = parse_add_command("/add @player123 A")
        assert not is_valid
        assert "ник" in error.lower()


class TestParseAcceptCommand:
    """Unit tests for /accept command parsing."""

    @pytest.mark.unit
    def test_valid_accept_command(self):
        """Test parsing of valid /accept command."""
        is_valid, username, error = parse_accept_command("/accept @player123")
        assert is_valid
        assert username == "@player123"
        assert error == ""

    @pytest.mark.unit
    def test_accept_command_without_at_symbol(self):
        """Test that username without @ is normalized."""
        is_valid, username, error = parse_accept_command("/accept player123")
        assert is_valid
        assert username == "@player123"

    @pytest.mark.unit
    def test_accept_command_missing_username(self):
        """Test that command without username is invalid."""
        is_valid, username, error = parse_accept_command("/accept")
        assert not is_valid
        assert "формат" in error.lower()

    @pytest.mark.unit
    def test_accept_command_invalid_username(self):
        """Test that command with invalid username is rejected."""
        is_valid, username, error = parse_accept_command("/accept @ab")
        assert not is_valid
        assert "username" in error.lower()


class TestSanitizeFilename:
    """Unit tests for filename sanitization."""

    @pytest.mark.unit
    def test_removes_invalid_characters(self):
        """Test that invalid filename characters are removed."""
        assert "/" not in sanitize_filename("test/file.txt")
        assert "\\" not in sanitize_filename("test\\file.txt")
        assert ":" not in sanitize_filename("test:file.txt")

    @pytest.mark.unit
    def test_limits_length(self):
        """Test that filename is limited to 255 characters."""
        long_name = "a" * 300
        sanitized = sanitize_filename(long_name)
        assert len(sanitized) <= 255

    @pytest.mark.unit
    def test_handles_empty_filename(self):
        """Test that empty filename gets default name."""
        assert sanitize_filename("") == "unnamed"
        assert sanitize_filename("   ") == "unnamed"

    @pytest.mark.unit
    def test_valid_filename_unchanged(self):
        """Test that valid filename is not modified."""
        filename = "screenshot_12345.jpg"
        assert sanitize_filename(filename) == filename
