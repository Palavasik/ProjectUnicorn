# -*- coding: utf-8 -*-
"""
Отправка служебных логов завершения сценария поиска в отдельный Telegram-чат.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from telegram import Bot

logger = logging.getLogger(__name__)


def format_duration_ru(seconds: float) -> str:
    """
    Человекочитаемая длительность на русском (минуты и секунды).

    Args:
        seconds: Неотрицательное число секунд.

    Returns:
        Строка вида «45 с» или «2 мин 15 с».
    """
    if seconds < 0:
        seconds = 0.0
    total = int(round(seconds))
    mins, sec = divmod(total, 60)
    if mins == 0:
        return f"{sec} с"
    if sec == 0:
        return f"{mins} мин"
    return f"{mins} мин {sec} с"


def format_job_completed_message(
    *,
    telegram_user_id: int,
    username: Optional[str],
    first_name: Optional[str],
    last_name: Optional[str],
    start_label: str,
    route_names: list[str],
    duration_seconds: Optional[float],
) -> str:
    """
    Текст сообщения в чат аналитики (plain text).

    Args:
        telegram_user_id: Числовой id пользователя Telegram.
        username: Username без @, если есть.
        first_name: Имя.
        last_name: Фамилия.
        start_label: Описание стартовой точки (геолокация или ввод).
        route_names: Названия маршрутов из ответа LLM.
        duration_seconds: Длительность сессии в секундах или None, если старт не зафиксирован.

    Returns:
        Готовый текст для send_message.
    """
    parts_name = []
    if first_name:
        parts_name.append(first_name)
    if last_name:
        parts_name.append(last_name)
    display_name = " ".join(parts_name) if parts_name else "—"
    uname = f"@{username}" if username else "—"

    lines = [
        "JOB завершён",
        f"Пользователь: id={telegram_user_id} {uname} ({display_name})",
        f"Старт: {start_label}",
    ]
    if route_names:
        lines.append("Маршруты: " + ", ".join(route_names))
    else:
        lines.append("Маршруты: (нет)")
    if duration_seconds is not None:
        lines.append(f"Длительность: {format_duration_ru(duration_seconds)}")
    else:
        lines.append("Длительность: —")

    return "\n".join(lines)


def _parse_chat_id(raw: str) -> int | str:
    """Преобразует строку из env в int для числовых id чатов."""
    s = raw.strip()
    if not s:
        return s
    if s.startswith("-") or s.isdigit():
        try:
            return int(s)
        except ValueError:
            pass
    return s


async def log_job_completed(
    bot: Bot,
    *,
    analytics_chat_id: Optional[str],
    telegram_user_id: int,
    username: Optional[str],
    first_name: Optional[str],
    last_name: Optional[str],
    start_label: str,
    route_names: list[str],
    duration_seconds: Optional[float],
) -> None:
    """
    Отправляет лог в чат аналитики. При отсутствии chat id или ошибке API не бросает наружу.

    Args:
        bot: Экземпляр бота python-telegram-bot.
        analytics_chat_id: ID чата из настроек или None.
        Остальные аргументы — данные для format_job_completed_message.
    """
    if not analytics_chat_id:
        return
    text = format_job_completed_message(
        telegram_user_id=telegram_user_id,
        username=username,
        first_name=first_name,
        last_name=last_name,
        start_label=start_label,
        route_names=route_names,
        duration_seconds=duration_seconds,
    )
    chat_id = _parse_chat_id(analytics_chat_id)
    try:
        await bot.send_message(
            chat_id=chat_id,
            text=text,
            disable_notification=True,
        )
    except Exception:
        logger.exception("Не удалось отправить лог аналитики в чат %s", analytics_chat_id)
