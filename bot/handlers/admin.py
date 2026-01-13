"""Admin handlers for managing players and registrations."""

import logging
from datetime import datetime

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from bot.handlers.decorators import admin_only
from config.settings import Settings
from database.database import Database
from database.repository import PlayerRepository
from models.player import Player

router = Router()
logger = logging.getLogger(__name__)


@router.callback_query(F.data.startswith("approve:"))
@admin_only
async def process_approve(callback: CallbackQuery, db: Database, settings: Settings) -> None:
    """
    Handle approval of pending registration.

    Args:
        callback: Callback query from approve button
        db: Database instance from dispatcher
        settings: Settings instance from dispatcher
    """

    # Extract telegram_id from callback data
    telegram_id = int(callback.data.split(":")[1])

    async for session in db.get_session():
        repo = PlayerRepository(session)

        # Get pending registration
        pending = await repo.get_pending(telegram_id)
        if not pending:
            await callback.answer("❌ Заявка не найдена.", show_alert=True)
            return

        # Check if already registered
        if await repo.check_player_exists(telegram_id):
            await callback.answer("❌ Пользователь уже зарегистрирован.", show_alert=True)
            await repo.remove_pending(telegram_id)
            return

        # Convert pending to player
        player = Player(
            telegram_id=pending.telegram_id,
            username=pending.username,
            nickname=pending.nickname,
            screenshot_path=pending.screenshot_path,
            registration_date=datetime.now().strftime("%Y-%m-%d"),
            status="Активен",
            added_by=f"@{callback.from_user.username or callback.from_user.id}",
            notes="Одобрено через бот",
        )

        # Add to database
        try:
            await repo.add_player(player)
            await repo.remove_pending(telegram_id)
            logger.info(f"Player {pending.username} approved by admin")
        except Exception as e:
            logger.error(f"Failed to approve player: {e}")
            await callback.answer("❌ Ошибка при одобрении заявки.", show_alert=True)
            return

    # Notify user
    try:
        await callback.bot.send_message(
            chat_id=telegram_id,
            text=(
                "🎉 <b>Поздравляем!</b>\n\n"
                "Ваша заявка на вступление в клан одобрена!\n"
                f"Добро пожаловать, <b>{pending.nickname}</b>!"
            ),
        )
    except Exception as e:
        logger.warning(f"Failed to notify user {telegram_id}: {e}")

    # Update admin message
    await callback.message.edit_caption(
        caption=f"{callback.message.caption}\n\n✅ <b>Одобрено</b> администратором {callback.from_user.username}",
        reply_markup=None,
    )
    await callback.answer("✅ Заявка одобрена!")


@router.callback_query(F.data.startswith("reject:"))
@admin_only
async def process_reject(callback: CallbackQuery, db: Database, settings: Settings) -> None:
    """
    Handle rejection of pending registration.

    Args:
        callback: Callback query from reject button
        db: Database instance from dispatcher
        settings: Settings instance from dispatcher
    """

    # Extract telegram_id from callback data
    telegram_id = int(callback.data.split(":")[1])

    async for session in db.get_session():
        repo = PlayerRepository(session)

        # Get pending registration
        pending = await repo.get_pending(telegram_id)
        if not pending:
            await callback.answer("❌ Заявка не найдена.", show_alert=True)
            return

        # Remove from pending
        try:
            await repo.remove_pending(telegram_id)
            logger.info(f"Player {pending.username} rejected by admin")
        except Exception as e:
            logger.error(f"Failed to reject player: {e}")
            await callback.answer("❌ Ошибка при отклонении заявки.", show_alert=True)
            return

    # Notify user
    try:
        await callback.bot.send_message(
            chat_id=telegram_id,
            text=(
                "❌ К сожалению, ваша заявка на вступление в клан отклонена.\n\n"
                "Вы можете попробовать зарегистрироваться снова позже: /register"
            ),
        )
    except Exception as e:
        logger.warning(f"Failed to notify user {telegram_id}: {e}")

    # Update admin message
    await callback.message.edit_caption(
        caption=f"{callback.message.caption}\n\n❌ <b>Отклонено</b> администратором {callback.from_user.username}",
        reply_markup=None,
    )
    await callback.answer("❌ Заявка отклонена.")


@router.message(Command("pending"))
@admin_only
async def cmd_pending(message: Message, db: Database, settings: Settings) -> None:
    """
    Show all pending registrations.

    Args:
        message: Incoming message
        db: Database instance from dispatcher
        settings: Settings instance from dispatcher
    """

    async for session in db.get_session():
        repo = PlayerRepository(session)
        pending_list = await repo.get_all_pending()

    if not pending_list:
        await message.answer("📭 Нет ожидающих заявок.")
        return

    response = "📋 <b>Ожидающие заявки:</b>\n\n"
    for pending in pending_list:
        response += (
            f"👤 {pending.username}\n"
            f"🎮 Никнейм: <b>{pending.nickname}</b>\n"
            f"🆔 ID: <code>{pending.telegram_id}</code>\n"
            f"📅 Дата: {pending.timestamp}\n"
            f"{'─' * 30}\n"
        )

    await message.answer(response)


@router.message(Command("list"))
@admin_only
async def cmd_list(message: Message, db: Database, settings: Settings) -> None:
    """
    Show all registered players.

    Args:
        message: Incoming message
        db: Database instance from dispatcher
        settings: Settings instance from dispatcher
    """

    async for session in db.get_session():
        repo = PlayerRepository(session)
        players = await repo.get_all_players()

    if not players:
        await message.answer("📭 Нет зарегистрированных игроков.")
        return

    # Separate active and excluded players
    active_players = [p for p in players if p.status == "Активен"]
    excluded_players = [p for p in players if p.status == "Отчислен"]

    response = f"👥 <b>Всего игроков: {len(players)}</b>\n\n"

    if active_players:
        response += f"✅ <b>Активные ({len(active_players)}):</b>\n"
        for player in active_players[:20]:  # Limit to 20 to avoid message too long
            response += f"• {player.nickname} ({player.username})\n"
        if len(active_players) > 20:
            response += f"... и еще {len(active_players) - 20}\n"
        response += "\n"

    if excluded_players:
        response += f"❌ <b>Отчисленные ({len(excluded_players)}):</b>\n"
        for player in excluded_players[:10]:
            response += f"• {player.nickname} ({player.username})\n"
        if len(excluded_players) > 10:
            response += f"... и еще {len(excluded_players) - 10}\n"

    await message.answer(response)


@router.message(Command("exclude"))
@admin_only
async def cmd_exclude(message: Message, db: Database, settings: Settings) -> None:
    """
    Exclude player from clan.

    Usage: /exclude @username reason

    Args:
        message: Incoming message
        db: Database instance from dispatcher
        settings: Settings instance from dispatcher
    """

    # Parse command
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        await message.answer(
            "❌ Неверный формат команды.\n\n"
            "Использование: /exclude @username причина\n"
            "Пример: /exclude @player123 Нарушение правил клана"
        )
        return

    username = parts[1]
    reason = parts[2]

    # Normalize username
    from utils.validators import normalize_username
    username = normalize_username(username)

    async for session in db.get_session():
        repo = PlayerRepository(session)

        # Find player by username
        players = await repo.get_all_players()
        player = next((p for p in players if p.username == username), None)

        if not player:
            await message.answer(f"❌ Игрок {username} не найден в базе данных.")
            return

        if player.status == "Отчислен":
            await message.answer(f"❌ Игрок {username} уже отчислен.")
            return

        # Exclude player
        try:
            excluded_by = f"@{message.from_user.username or message.from_user.id}"
            await repo.exclude_player(player.telegram_id, reason, excluded_by)
            logger.info(f"Player {username} excluded by {excluded_by}")
        except Exception as e:
            logger.error(f"Failed to exclude player: {e}")
            await message.answer("❌ Ошибка при отчислении игрока.")
            return

    # Notify player
    try:
        await message.bot.send_message(
            chat_id=player.telegram_id,
            text=(
                f"❌ Вы были отчислены из клана.\n\n"
                f"<b>Причина:</b> {reason}\n\n"
                "Если у вас есть вопросы, обратитесь к администрации клана."
            ),
        )
    except Exception as e:
        logger.warning(f"Failed to notify excluded player {player.telegram_id}: {e}")

    await message.answer(
        f"✅ Игрок {player.nickname} ({username}) отчислен из клана.\n"
        f"<b>Причина:</b> {reason}"
    )
