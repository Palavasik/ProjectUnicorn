"""
Тесты форматирования логов аналитики (Telegram).
"""

import pytest

from services.analytics_telegram import (
    format_duration_ru,
    format_job_completed_message,
)


def test_format_duration_ru_seconds_only():
    assert format_duration_ru(44.4) == "44 с"
    assert format_duration_ru(0) == "0 с"


def test_format_duration_ru_minutes():
    assert format_duration_ru(125) == "2 мин 5 с"
    assert format_duration_ru(120) == "2 мин"


def test_format_job_completed_message_full():
    text = format_job_completed_message(
        telegram_user_id=42,
        username="runner",
        first_name="Иван",
        last_name="Петров",
        start_label="геолокация: 55.755800, 37.617300",
        route_names=["Набережная", "Парк"],
        duration_seconds=90.0,
    )
    assert "JOB завершён" in text
    assert "id=42" in text
    assert "@runner" in text
    assert "Иван Петров" in text
    assert "геолокация: 55.755800, 37.617300" in text
    assert "Набережная" in text and "Парк" in text
    assert "1 мин 30 с" in text


def test_format_job_completed_message_empty_routes_and_no_duration():
    text = format_job_completed_message(
        telegram_user_id=1,
        username=None,
        first_name=None,
        last_name=None,
        start_label="—",
        route_names=[],
        duration_seconds=None,
    )
    assert "Маршруты: (нет)" in text
    assert "Длительность: —" in text
    assert "Пользователь: id=1 —" in text
