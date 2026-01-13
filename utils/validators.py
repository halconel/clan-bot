import re
from typing import Tuple


def validate_nickname(nickname: str) -> Tuple[bool, str]:
    """
    Validate player nickname.

    Rules:
    - Length: 1-15 characters (as per Kingdom Clash game requirements)
    - Any characters allowed (including special characters and emojis)

    Args:
        nickname: Player's in-game nickname

    Returns:
        Tuple of (is_valid, error_message)
        - (True, "") if valid
        - (False, "error message") if invalid
    """
    if not nickname or not nickname.strip():
        return False, "Ник не может быть пустым"

    nickname = nickname.strip()

    if len(nickname) < 1:
        return False, "Ник не может быть пустым"

    if len(nickname) > 15:
        return False, "Ник слишком длинный. Максимум 15 символов"

    return True, ""


def validate_username(username: str) -> Tuple[bool, str]:
    """
    Validate Telegram username.

    Rules:
    - Must start with @
    - Length: 5-32 characters (including @)
    - Allowed: letters, numbers, underscores
    - No special characters

    Args:
        username: Telegram username (with or without @)

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not username or not username.strip():
        return False, "Username не может быть пустым"

    username = username.strip()

    # Add @ if missing
    if not username.startswith('@'):
        username = '@' + username

    if len(username) < 6:  # @ + min 5 chars
        return False, "Username слишком короткий"

    if len(username) > 33:  # @ + max 32 chars
        return False, "Username слишком длинный"

    # Check format: @username (letters, numbers, underscores only)
    pattern = r'^@[a-zA-Z0-9_]+$'
    if not re.match(pattern, username):
        return False, "Неверный формат username. Используйте @username"

    return True, ""


def normalize_username(username: str) -> str:
    """
    Normalize username by ensuring it starts with @.

    Args:
        username: Telegram username (with or without @)

    Returns:
        Username with @ prefix
    """
    username = username.strip()
    if not username.startswith('@'):
        return '@' + username
    return username


def parse_add_command(text: str) -> Tuple[bool, str, str, str]:
    """
    Parse /add command arguments.

    Expected format: /add @username НикИгрока

    Args:
        text: Full command text

    Returns:
        Tuple of (is_valid, username, nickname, error_message)
    """
    parts = text.split(maxsplit=2)

    if len(parts) < 3:
        return False, "", "", "Неверный формат. Используйте: /add @username НикИгрока"

    command, username, nickname = parts

    # Validate username
    is_valid_username, username_error = validate_username(username)
    if not is_valid_username:
        return False, "", "", f"Ошибка в username: {username_error}"

    # Validate nickname
    is_valid_nickname, nickname_error = validate_nickname(nickname)
    if not is_valid_nickname:
        return False, "", "", f"Ошибка в нике: {nickname_error}"

    return True, normalize_username(username), nickname.strip(), ""


def parse_accept_command(text: str) -> Tuple[bool, str, str]:
    """
    Parse /accept command arguments.

    Expected format: /accept @username

    Args:
        text: Full command text

    Returns:
        Tuple of (is_valid, username, error_message)
    """
    parts = text.split(maxsplit=1)

    if len(parts) < 2:
        return False, "", "Неверный формат. Используйте: /accept @username"

    command, username = parts

    # Validate username
    is_valid_username, username_error = validate_username(username)
    if not is_valid_username:
        return False, "", f"Ошибка в username: {username_error}"

    return True, normalize_username(username), ""


def extract_username_from_user(user) -> str:
    """
    Extract username from Telegram User object.

    Args:
        user: Telegram User object (from aiogram)

    Returns:
        Username with @ prefix, or empty string if no username
    """
    if hasattr(user, 'username') and user.username:
        return '@' + user.username
    return ""


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename by removing/replacing invalid characters.

    Args:
        filename: Original filename

    Returns:
        Sanitized filename safe for filesystem
    """
    # Remove or replace invalid filename characters
    invalid_chars = r'[<>:"/\\|?*]'
    sanitized = re.sub(invalid_chars, '_', filename)

    # Remove leading/trailing spaces and dots
    sanitized = sanitized.strip('. ')

    # Limit length
    max_length = 255
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]

    return sanitized or "unnamed"
