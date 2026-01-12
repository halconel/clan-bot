"""Common bot handlers (start, help, etc.)."""

import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

router = Router()
logger = logging.getLogger(__name__)


@router.message(Command("start"))
async def cmd_start(message: Message) -> None:
    """
    Handle /start command.

    Args:
        message: Incoming message
    """
    await message.answer(
        "👋 Добро пожаловать в бот регистрации клана!\n\n"
        "Чтобы зарегистрироваться, используйте команду /register\n"
        "Для помощи используйте /help"
    )


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    """
    Handle /help command.

    Args:
        message: Incoming message
    """
    help_text = """
📋 <b>Доступные команды:</b>

<b>Для игроков:</b>
/start - Начать работу с ботом
/register - Зарегистрироваться в клане
/help - Показать эту справку

<b>Для администраторов:</b>
/pending - Показать ожидающие заявки
/list - Показать список всех игроков
/exclude @username причина - Отчислить игрока из клана

<b>Процесс регистрации:</b>
1. Отправьте команду /register
2. Укажите ваш игровой никнейм
3. Отправьте скриншот профиля в игре
4. Дождитесь одобрения администратором
"""
    await message.answer(help_text)


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    """
    Cancel current operation and reset FSM state.

    Args:
        message: Incoming message
        state: FSM context
    """
    current_state = await state.get_state()

    if current_state is None:
        await message.answer("❌ Нет активной операции для отмены.")
        return

    await state.clear()
    logger.info(f"User {message.from_user.id} cancelled operation from state {current_state}")
    await message.answer(
        "✅ Операция отменена.\n\n"
        "Используйте /register для новой регистрации или /help для справки."
    )
