"""Handlers for player registration process."""

import logging
from datetime import datetime

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.keyboards.admin import get_approve_reject_keyboard
from bot.states.registration import RegistrationStates
from database.database import Database
from database.repository import PlayerRepository
from models.player import PendingRegistration

router = Router()
logger = logging.getLogger(__name__)


@router.message(Command("register"))
async def cmd_register(message: Message, state: FSMContext) -> None:
    """
    Start registration process.

    Args:
        message: Incoming message
        state: FSM context
    """
    # Get database from dispatcher
    db: Database = message.bot.get("db")

    # Check if user is already registered or has pending request
    async for session in db.get_session():
        repo = PlayerRepository(session)

        # Check if already registered
        if await repo.check_player_exists(message.from_user.id):
            await message.answer(
                "❌ Вы уже зарегистрированы в клане!\n"
                "Используйте /help для просмотра доступных команд."
            )
            return

        # Check if has pending request
        pending = await repo.get_pending(message.from_user.id)
        if pending:
            await message.answer(
                "⏳ Ваша заявка уже отправлена и ожидает рассмотрения.\n"
                "Пожалуйста, дождитесь ответа от администратора."
            )
            return

    # Start registration process
    await message.answer(
        "📝 Начинаем регистрацию!\n\n"
        "Пожалуйста, отправьте ваш <b>игровой никнейм</b>.\n"
        "Это имя, которое отображается в игре."
    )
    await state.set_state(RegistrationStates.waiting_for_nickname)


@router.message(RegistrationStates.waiting_for_nickname, F.text)
async def process_nickname(message: Message, state: FSMContext) -> None:
    """
    Process nickname input.

    Args:
        message: Incoming message with nickname
        state: FSM context
    """
    from utils.validators import validate_nickname

    nickname = message.text.strip()

    # Validate nickname
    is_valid, error = validate_nickname(nickname)
    if not is_valid:
        await message.answer(f"❌ {error}\n\nПожалуйста, отправьте корректный никнейм:")
        return

    # Save nickname to FSM storage
    await state.update_data(nickname=nickname)

    await message.answer(
        f"✅ Никнейм <b>{nickname}</b> принят!\n\n"
        "Теперь отправьте <b>скриншот вашего профиля</b> в игре.\n"
        "Скриншот должен четко показывать ваш никнейм и уровень."
    )
    await state.set_state(RegistrationStates.waiting_for_screenshot)


@router.message(RegistrationStates.waiting_for_screenshot, F.photo)
async def process_screenshot(message: Message, state: FSMContext) -> None:
    """
    Process screenshot upload.

    Args:
        message: Incoming message with photo
        state: FSM context
    """
    # Get user data from FSM
    data = await state.get_data()
    nickname = data.get("nickname")

    if not nickname:
        await message.answer("❌ Ошибка: никнейм не найден. Начните регистрацию заново: /register")
        await state.clear()
        return

    # Get the largest photo
    photo = message.photo[-1]
    file_id = photo.file_id

    # Get database and settings
    db: Database = message.bot.get("db")
    settings = message.bot.get("settings")

    # Save screenshot locally
    file = await message.bot.get_file(file_id)
    file_path = file.file_path

    # Generate unique filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    local_filename = f"screenshot_{message.from_user.id}_{timestamp}.jpg"
    local_path = f"{settings.storage.screenshots_dir}/{local_filename}"

    # Download file
    await message.bot.download_file(file_path, local_path)
    logger.info(f"Screenshot saved: {local_path}")

    # Create pending registration
    username = message.from_user.username or f"user_{message.from_user.id}"
    if not username.startswith("@"):
        username = f"@{username}"

    pending = PendingRegistration(
        telegram_id=message.from_user.id,
        username=username,
        nickname=nickname,
        screenshot_path=local_path,
    )

    # Save to database
    async for session in db.get_session():
        repo = PlayerRepository(session)
        try:
            await repo.save_pending(pending)
            logger.info(f"Pending registration saved for {username}")
        except Exception as e:
            logger.error(f"Failed to save pending registration: {e}")
            await message.answer(
                "❌ Произошла ошибка при сохранении заявки. "
                "Пожалуйста, попробуйте позже или обратитесь к администратору."
            )
            await state.clear()
            return

    # Send notification to admin
    admin_message = (
        f"🆕 <b>Новая заявка на регистрацию!</b>\n\n"
        f"👤 Пользователь: {username}\n"
        f"🎮 Никнейм: <b>{nickname}</b>\n"
        f"🆔 Telegram ID: <code>{message.from_user.id}</code>\n\n"
        f"📸 Скриншот прикреплен ниже."
    )

    try:
        # Send notification with screenshot to admin
        await message.bot.send_photo(
            chat_id=settings.telegram.leader_telegram_id,
            photo=file_id,
            caption=admin_message,
            reply_markup=get_approve_reject_keyboard(message.from_user.id),
        )
        logger.info(f"Admin notification sent for {username}")
    except Exception as e:
        logger.error(f"Failed to send admin notification: {e}")

    # Confirm to user
    await message.answer(
        "✅ <b>Заявка отправлена!</b>\n\n"
        "Ваша заявка успешно отправлена администратору клана.\n"
        "Ожидайте одобрения. Вы получите уведомление, когда администратор рассмотрит вашу заявку.\n\n"
        f"📝 Ваш никнейм: <b>{nickname}</b>"
    )

    # Clear FSM state
    await state.clear()


@router.message(RegistrationStates.waiting_for_screenshot)
async def invalid_screenshot(message: Message) -> None:
    """
    Handle invalid screenshot (not a photo).

    Args:
        message: Incoming message
    """
    await message.answer(
        "❌ Пожалуйста, отправьте <b>фотографию</b> (скриншот).\n\n"
        "Если вы хотите начать регистрацию заново, используйте команду /register"
    )
