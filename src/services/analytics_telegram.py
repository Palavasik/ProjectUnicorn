# -*- coding: utf-8 -*-
"""
Отправка служебных логов завершения сценария поиска в отдельный Telegram-чат.
"""

from __future__ import annotations

import html
import logging
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from telegram import Bot

logger = logging.getLogger(__name__)

# Лимит Telegram на длину одного текстового сообщения
_TELEGRAM_TEXT_MAX = 4096


def _html_escape(text: str) -> str:
    """Экранирование для Telegram HTML (parse_mode=HTML)."""
    return html.escape(text, quote=False)


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
    Текст сообщения в чат аналитики (HTML + пиктограммы для parse_mode=HTML).

    Args:
        telegram_user_id: Числовой id пользователя Telegram.
        username: Username без @, если есть.
        first_name: Имя.
        last_name: Фамилия.
        start_label: Описание стартовой точки (геолокация или ввод).
        route_names: Названия маршрутов из ответа LLM.
        duration_seconds: Длительность сессии в секундах или None, если старт не зафиксирован.

    Returns:
        Готовый текст для send_message с parse_mode=\"HTML\".
    """
    parts_name = []
    if first_name:
        parts_name.append(first_name)
    if last_name:
        parts_name.append(last_name)
    display_name = " ".join(parts_name) if parts_name else "—"
    uname_line = f"@{_html_escape(username)}" if username else "—"

    uid = _html_escape(str(telegram_user_id))
    disp = _html_escape(display_name)
    start_safe = _html_escape(start_label.strip() or "—")

    lines: list[str] = [
        "✅ <b>JOB завершён</b>",
        "━━━━━━━━━━━━━━━━━━━━",
        "",
        "👤 <b>Пользователь</b>",
        f"   • ID: <code>{uid}</code>",
        f"   • Username: {uname_line}",
        f"   • Имя: {disp}",
        "",
        "📍 <b>Стартовая точка</b>",
        f"   {start_safe}",
        "",
        "🛤 <b>Маршруты</b>",
    ]
    if route_names:
        for i, name in enumerate(route_names, 1):
            lines.append(f"   {i}. {_html_escape(name)}")
    else:
        lines.append("   <i>нет вариантов</i>")
    lines.extend(["", "⏱ <b>Длительность сессии</b>"])
    if duration_seconds is not None:
        lines.append(f"   {_html_escape(format_duration_ru(duration_seconds))}")
    else:
        lines.append("   <i>не зафиксирована</i>")

    return "\n".join(lines)


def truncate_for_telegram_log(text: str, max_len: int = _TELEGRAM_TEXT_MAX - 200) -> str:
    """
    Укоротить текст для одного сообщения Telegram (запас под заголовок).

    Args:
        text: Исходный текст.
        max_len: Максимальная длина тела (символов).

    Returns:
        Исходная строка или обрезанная с пометкой.
    """
    if len(text) <= max_len:
        return text
    return text[: max(0, max_len - 40)] + "\n… [обрезано]"


def format_llm_response_message(
    *,
    telegram_user_id: int,
    prompt_text: str,
    raw_content: str,
    model_name: Optional[str] = None,
) -> str:
    """
    Текст второго сообщения в аналитику: запрос и сырой ответ LLM (HTML + два блока pre).

    Args:
        telegram_user_id: id пользователя (связка с первым сообщением).
        prompt_text: Полный текст user-сообщения, отправленного в Chat Completions.
        raw_content: Полное содержимое message.content от API.
        model_name: Имя модели OpenRouter (опционально).

    Returns:
        Текст для send_message с parse_mode=\"HTML\".
    """
    # Делим лимит сообщения между запросом и ответом (заголовки ~400 символов)
    _chunk = 1650
    req = truncate_for_telegram_log(
        prompt_text.strip() or "—",
        max_len=_chunk,
    )
    body = truncate_for_telegram_log(
        raw_content.strip() or "—",
        max_len=_chunk,
    )
    req_safe = _html_escape(req)
    body_safe = _html_escape(body)
    uid = _html_escape(str(telegram_user_id))
    model_line = ""
    if model_name:
        model_line = f"🎯 <b>Модель</b>: <code>{_html_escape(model_name)}</code>\n"
    return (
        "🤖 <b>LLM: запрос и ответ</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"🔗 <b>Связка</b> · <code>user_id={uid}</code>\n"
        f"{model_line}"
        "\n"
        "📤 <b>Запрос</b> (текст в API)\n"
        f"<pre>{req_safe}</pre>\n"
        "\n"
        "📥 <b>Ответ</b> (message.content)\n"
        f"<pre>{body_safe}</pre>"
    )


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
            parse_mode="HTML",
            disable_notification=True,
        )
    except Exception:
        logger.exception("Не удалось отправить лог аналитики в чат %s", analytics_chat_id)


async def log_llm_response(
    bot: Bot,
    *,
    analytics_chat_id: Optional[str],
    telegram_user_id: int,
    prompt_text: str,
    raw_content: str,
    model_name: Optional[str] = None,
) -> None:
    """
    Второе сообщение в чат аналитики: текст запроса к модели и полный ответ (до лимита Telegram).

    При отсутствии chat id или ошибке API не бросает наружу.
    """
    if not analytics_chat_id:
        return
    text = format_llm_response_message(
        telegram_user_id=telegram_user_id,
        prompt_text=prompt_text,
        raw_content=raw_content,
        model_name=model_name,
    )
    if len(text) > _TELEGRAM_TEXT_MAX:
        text = text[: _TELEGRAM_TEXT_MAX - 40] + "\n<i>… [обрезано]</i>"
    chat_id = _parse_chat_id(analytics_chat_id)
    try:
        await bot.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode="HTML",
            disable_notification=True,
        )
    except Exception:
        logger.exception("Не удалось отправить ответ LLM в чат аналитики %s", analytics_chat_id)
