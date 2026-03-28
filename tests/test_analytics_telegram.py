"""
Тесты форматирования логов аналитики (Telegram).
"""

import pytest

from services.analytics_telegram import (
    format_duration_ru,
    format_job_completed_message,
    format_llm_latency,
    format_llm_response_message,
    truncate_for_telegram_log,
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
    assert "JOB" in text and "завершён" in text
    assert "<code>42</code>" in text
    assert "@runner" in text
    assert "Иван" in text and "Петров" in text
    assert "геолокация" in text
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
    assert "нет вариантов" in text
    assert "не зафиксирована" in text
    assert "<code>1</code>" in text


def test_truncate_for_telegram_log():
    short = "abc"
    assert truncate_for_telegram_log(short, max_len=100) == short
    long = "x" * 500
    out = truncate_for_telegram_log(long, max_len=100)
    assert len(out) < len(long)
    assert "обрезано" in out


def test_format_llm_latency():
    assert format_llm_latency(1.234) == "1.23 с"
    assert format_llm_latency(0) == "0.00 с"


def test_format_llm_response_message():
    text = format_llm_response_message(
        telegram_user_id=99,
        prompt_text="Старт: 55, 37. Дистанция: 10 км.",
        raw_content='{"routes": []}',
        model_name="test/model",
        llm_duration_seconds=2.5,
    )
    assert "LLM" in text and "запрос" in text.lower()
    assert "Запрос" in text and "Ответ" in text
    assert "Время ответа LLM" in text
    assert "2.50 с" in text
    assert "user_id=" in text and "99" in text
    assert "<pre>" in text
    assert "routes" in text
    assert "55, 37" in text or "Старт" in text
    assert "test/model" in text
