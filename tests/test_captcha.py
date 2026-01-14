"""Tests for captcha module."""

import json

import pytest

from utils.captcha import (
    CaptchaQuestion,
    generate_captcha,
    get_captcha_explanation,
    get_captcha_keyboard_data,
    get_questions,
    load_questions,
    validate_captcha_answer,
)


class TestCaptchaQuestion:
    """Test CaptchaQuestion dataclass."""

    def test_get_shuffled_options(self):
        """Test that options are shuffled."""
        question = CaptchaQuestion(question="Test?", correct_answer="A", wrong_answers=["B", "C"])
        options = question.get_shuffled_options()

        assert len(options) == 3
        assert "A" in options
        assert "B" in options
        assert "C" in options

    def test_is_correct(self):
        """Test answer validation."""
        question = CaptchaQuestion(
            question="Test?", correct_answer="correct", wrong_answers=["wrong1", "wrong2"]
        )

        assert question.is_correct("correct")
        assert question.is_correct("CORRECT")  # Case insensitive
        assert question.is_correct("  correct  ")  # Strips whitespace
        assert not question.is_correct("wrong1")
        assert not question.is_correct("wrong2")


class TestLoadQuestions:
    """Test question loading from JSON."""

    def test_load_questions_from_file(self, tmp_path):
        """Test loading questions from JSON file."""
        # Create test questions file
        test_data = [
            {"question": "Q1?", "correct": "A1", "wrong": ["W1", "W2"]},
            {"question": "Q2?", "correct": "A2", "wrong": ["W3", "W4"]},
        ]

        test_file = tmp_path / "test_questions.json"
        with open(test_file, "w", encoding="utf-8") as f:
            json.dump(test_data, f)

        # Load questions
        questions = load_questions(test_file)

        assert len(questions) == 2
        assert questions[0].question == "Q1?"
        assert questions[0].correct_answer == "A1"
        assert questions[0].wrong_answers == ["W1", "W2"]

    def test_load_questions_file_not_found(self):
        """Test error when file doesn't exist."""
        with pytest.raises(FileNotFoundError):
            load_questions("nonexistent.json")


class TestGenerateCaptcha:
    """Test captcha generation."""

    def test_generate_captcha_returns_question(self):
        """Test that generate_captcha returns a valid question."""
        captcha = generate_captcha()

        assert isinstance(captcha, CaptchaQuestion)
        assert len(captcha.question) > 0
        assert len(captcha.correct_answer) > 0
        assert len(captcha.wrong_answers) == 2

    def test_generate_captcha_randomness(self):
        """Test that generate_captcha returns different questions."""
        questions = [generate_captcha().question for _ in range(10)]

        # Should have at least 2 different questions in 10 attempts
        assert len(set(questions)) >= 2


class TestGetCaptchaKeyboardData:
    """Test keyboard data generation."""

    def test_get_captcha_keyboard_data_format(self):
        """Test keyboard data format."""
        question = CaptchaQuestion(question="Test?", correct_answer="A", wrong_answers=["B", "C"])

        keyboard_data = get_captcha_keyboard_data(question)

        assert len(keyboard_data) == 3
        for text, callback_data in keyboard_data:
            assert text in ["A", "B", "C"]
            assert callback_data.startswith("captcha:")
            assert callback_data.split(":")[1] in ["A", "B", "C"]


class TestValidateCaptchaAnswer:
    """Test answer validation."""

    def test_validate_correct_answer(self):
        """Test validation of correct answer."""
        question = CaptchaQuestion(
            question="Test?", correct_answer="correct", wrong_answers=["wrong1", "wrong2"]
        )

        assert validate_captcha_answer(question, "correct")
        assert validate_captcha_answer(question, "CORRECT")
        assert validate_captcha_answer(question, "  correct  ")

    def test_validate_wrong_answer(self):
        """Test validation of wrong answer."""
        question = CaptchaQuestion(
            question="Test?", correct_answer="correct", wrong_answers=["wrong1", "wrong2"]
        )

        assert not validate_captcha_answer(question, "wrong1")
        assert not validate_captcha_answer(question, "wrong2")
        assert not validate_captcha_answer(question, "random")


class TestGetCaptchaExplanation:
    """Test explanation text."""

    def test_get_captcha_explanation_contains_key_phrases(self):
        """Test that explanation contains important information."""
        explanation = get_captcha_explanation()

        assert "безопасност" in explanation.lower()
        assert "бот" in explanation.lower()
        assert "спам" in explanation.lower()


class TestGetQuestions:
    """Test get_questions caching."""

    def test_get_questions_returns_list(self):
        """Test that get_questions returns a list of questions."""
        questions = get_questions()

        assert isinstance(questions, list)
        assert len(questions) > 0
        assert all(isinstance(q, CaptchaQuestion) for q in questions)

    def test_get_questions_caches_result(self):
        """Test that get_questions caches the result."""
        questions1 = get_questions()
        questions2 = get_questions()

        # Should return the same list object (cached)
        assert questions1 is questions2
