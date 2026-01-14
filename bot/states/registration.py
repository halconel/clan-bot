"""FSM states for player registration process."""

from aiogram.fsm.state import State, StatesGroup


class RegistrationStates(StatesGroup):
    """States for player registration flow."""

    waiting_for_captcha = State()
    waiting_for_nickname = State()
    waiting_for_screenshot = State()
