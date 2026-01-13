from typing import Optional

from models.player import PendingRegistration, Player


def format_welcome_message() -> str:
    """Format welcome message for /start command."""
    return (
        "Добро пожаловать в бот клана Kingdom Clash!\n\n"
        "Для регистрации мне нужна следующая информация:\n"
        "1. Ваш игровой ник\n"
        "2. Скриншот вашего профиля в игре\n\n"
        "Давайте начнем! Пожалуйста, отправьте ваш игровой ник."
    )


def format_nickname_prompt() -> str:
    """Format prompt for nickname input."""
    return (
        "Пожалуйста, отправьте ваш игровой ник.\n\n"
        "Требования:\n"
        "- От 3 до 20 символов\n"
        "- Буквы, цифры, пробелы, _ и -"
    )


def format_screenshot_prompt(nickname: str) -> str:
    """
    Format prompt for screenshot upload.

    Args:
        nickname: Player's nickname
    """
    return (
        f"Отлично, {nickname}!\n\n"
        "Теперь отправьте скриншот вашего профиля в игре.\n\n"
        "Важно: отправьте именно фото (не файл)."
    )


def format_registration_pending(nickname: str) -> str:
    """
    Format message when registration is submitted.

    Args:
        nickname: Player's nickname
    """
    return (
        f"Спасибо, {nickname}!\n\n"
        "Ваша заявка отправлена главе клана на рассмотрение.\n"
        "Вы получите уведомление, когда заявка будет рассмотрена."
    )


def format_registration_approved() -> str:
    """Format message when registration is approved."""
    return "Поздравляем! Вы приняты в клан Kingdom Clash! 🎉\n\nДобро пожаловать в нашу команду!"


def format_registration_rejected(reason: Optional[str] = None) -> str:
    """
    Format message when registration is rejected.

    Args:
        reason: Optional rejection reason
    """
    message = "К сожалению, ваша заявка отклонена."

    if reason:
        message += f"\n\nПричина: {reason}"

    message += "\n\nВы можете попробовать подать заявку снова, отправив /start."

    return message


def format_already_registered() -> str:
    """Format message when user tries to register again."""
    return "Вы уже зарегистрированы в клане!\n\nИспользуйте /help для просмотра доступных команд."


def format_pending_registration_exists() -> str:
    """Format message when user has pending registration."""
    return (
        "Ваша заявка уже отправлена и ожидает рассмотрения главой клана.\n\n"
        "Пожалуйста, дождитесь результата."
    )


def format_leader_notification(pending: PendingRegistration) -> str:
    """
    Format notification for leader about new registration.

    Args:
        pending: Pending registration data
    """
    return (
        f"Новая заявка на вступление:\n\n"
        f"👤 Username: {pending.username}\n"
        f"🎮 Игровой ник: {pending.nickname}\n"
        f"📅 Дата заявки: {pending.timestamp}\n\n"
        f"Используйте кнопки ниже для принятия решения."
    )


def format_approval_success(player: Player) -> str:
    """
    Format message after successful approval.

    Args:
        player: Approved player data
    """
    return f"Игрок {player.username} ({player.nickname}) успешно добавлен в клан!"


def format_rejection_success(username: str) -> str:
    """
    Format message after successful rejection.

    Args:
        username: Rejected user's username
    """
    return f"Заявка игрока {username} отклонена."


def format_no_pending_registration(username: str) -> str:
    """
    Format error message when no pending registration found.

    Args:
        username: Username to search for
    """
    return f"Заявка от пользователя {username} не найдена."


def format_manual_add_success(username: str, nickname: str) -> str:
    """
    Format message after successful manual add.

    Args:
        username: Player's username
        nickname: Player's nickname
    """
    return f"Игрок {username} ({nickname}) успешно добавлен в клан вручную!"


def format_player_already_exists(username: str) -> str:
    """
    Format error message when player already exists.

    Args:
        username: Player's username
    """
    return f"Игрок {username} уже находится в базе данных клана."


def format_help_message(is_leader: bool = False) -> str:
    """
    Format help message with available commands.

    Args:
        is_leader: Whether user is clan leader
    """
    message = (
        "Доступные команды:\n\n"
        "/start - Регистрация в клане\n"
        "/help - Показать это сообщение\n"
        "/cancel - Отменить текущую операцию\n"
    )

    if is_leader:
        message += (
            "\nКоманды главы клана:\n"
            "/accept @username - Одобрить заявку\n"
            "/add @username НикИгрока - Добавить игрока вручную\n"
        )

    return message


def format_operation_cancelled() -> str:
    """Format message when operation is cancelled."""
    return "Операция отменена.\n\nОтправьте /start для новой регистрации."


def format_access_denied() -> str:
    """Format message for unauthorized access."""
    return "Доступ запрещен. Эта команда доступна только главе клана."


def format_invalid_photo() -> str:
    """Format error message for invalid photo upload."""
    return (
        "Пожалуйста, отправьте скриншот как фото, а не как файл.\n\n"
        "Используйте кнопку прикрепления фото в Telegram."
    )


def format_error_message(error_text: str) -> str:
    """
    Format generic error message.

    Args:
        error_text: Error description
    """
    return f"Ошибка: {error_text}\n\nПопробуйте еще раз или обратитесь к администратору."


def format_google_sheets_error() -> str:
    """Format error message for Google Sheets connection issues."""
    return (
        "Произошла ошибка при сохранении данных.\n"
        "Глава клана уведомлен о проблеме.\n\n"
        "Пожалуйста, попробуйте позже."
    )
