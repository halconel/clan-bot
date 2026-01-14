"""CAPTCHA generation and validation for bot security.

Источники вопросов:
- https://www.today.com/life/inspiration/easy-trivia-questions-rcna194763
- https://www.opinionstage.com/blog/trivia-questions/
- https://www.quizbreaker.com/trivia-questions
"""

import json
import random
from dataclasses import dataclass
from pathlib import Path


@dataclass
class CaptchaQuestion:
    """Represents a captcha question with answer options."""

    question: str
    correct_answer: str
    wrong_answers: list[str]

    def get_shuffled_options(self) -> list[str]:
        """Return shuffled list of all answer options."""
        options = [self.correct_answer] + self.wrong_answers
        random.shuffle(options)
        return options

    def is_correct(self, answer: str) -> bool:
        """Check if provided answer is correct."""
        return answer.lower().strip() == self.correct_answer.lower().strip()


def load_questions(file_path: str | Path = "data/captcha_questions.json") -> list[CaptchaQuestion]:
    """Load captcha questions from JSON file."""
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Captcha questions file not found: {path}")

    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    questions = []
    for item in data:
        question = CaptchaQuestion(
            question=item["question"],
            correct_answer=item["correct"],
            wrong_answers=item["wrong"],
        )
        questions.append(question)

    return questions


# Global cache of questions (loaded once at module import)
_QUESTIONS_CACHE: list[CaptchaQuestion] | None = None


def get_questions() -> list[CaptchaQuestion]:
    """Get all captcha questions (cached)."""
    global _QUESTIONS_CACHE

    if _QUESTIONS_CACHE is None:
        _QUESTIONS_CACHE = load_questions()

    return _QUESTIONS_CACHE


def generate_captcha() -> CaptchaQuestion:
    """Generate a random captcha question."""
    questions = get_questions()
    return random.choice(questions)


def get_captcha_keyboard_data(question: CaptchaQuestion) -> list[tuple[str, str]]:
    """
    Get shuffled options for inline keyboard.

    Returns list of (button_text, callback_data) tuples.
    """
    options = question.get_shuffled_options()
    return [(option, f"captcha:{option}") for option in options]


def validate_captcha_answer(question: CaptchaQuestion, answer: str) -> bool:
    """Validate user's answer to captcha question."""
    return question.is_correct(answer)


def get_captcha_explanation() -> str:
    """Get explanation text for why captcha is needed."""
    return (
        "🛡 <b>Проверка безопасности</b>\n\n"
        "Для защиты от автоматических ботов и спама, пожалуйста, "
        "ответьте на простой вопрос. Это займет всего несколько секунд.\n\n"
        "<i>Это помогает нам поддерживать качество чата и защищает "
        "от нежелательных заявок.</i>"
    )
