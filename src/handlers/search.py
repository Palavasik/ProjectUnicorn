"""
Обработчики поиска маршрутов для бега.
"""

import asyncio
import html
import logging
import re
import time

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    Update,
)
from telegram.error import BadRequest
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from config.settings import Settings
from handlers.commands import (
    BUTTON_CANCEL,
    BUTTON_FIND,
    BUTTON_MAIN,
    get_main_keyboard,
    get_start_message,
    start_handler,
)
from services.analytics_telegram import log_job_completed, log_llm_response
from services.geocode_service import GeocodeUnavailableError, geocode_to_lat_lon
from services.llm_route_service import LLMRouteServiceError, get_routes_from_llm
from services.supabase_client import insert_feedback
from utils.map_links import build_yandex_route_link

logger = logging.getLogger(__name__)

# Состояния диалога: стартовая точка -> дистанция -> результаты
LOCATION, DISTANCE = range(2)

# Варианты дистанции: callback_data -> (подпись кнопки, значение в км)
DISTANCE_OPTIONS = [
    ("short", "Короткая (3–5 км)", 4),
    ("daily", "Ежедневная (10 км)", 10),
    ("long", "Длинная (18–20 км)", 19),
]
DISTANCE_KM_BY_KEY = {key: km for key, _label, km in DISTANCE_OPTIONS}

# Сообщение на время запроса к LLM (inline-кнопки дистанции убираются)
_DISTANCE_LOADING_TEXT = "⏳ Подбираем маршруты…"

# Обратная связь после выдачи списка маршрутов: (оценка, подпись кнопки)
FEEDBACK_OPTIONS = [(5, "Отлично"), (3, "Норм"), (1, "Не зашло")]

# Значение route_name в БД для отзыва о подборке (без привязки к одному маршруту)
FEEDBACK_SEARCH_ROUTE_NAME = "Подбор маршрутов"
# Ожидается ответ на inline «Как вам подбор маршрутов?» после успешного LLM
FEEDBACK_SEARCH_SESSION_KEY = "feedback_search_session_pending"

# Метрики сессии поиска (лог в ANALYTICS_CHAT_ID)
JOB_STARTED_AT_KEY = "job_started_at_perf"
SEARCH_START_LABEL_KEY = "search_start_label"

_SEARCH_STATE_KEYS = (
    "search_start_lat",
    "search_start_lon",
    "search_distance",
    FEEDBACK_SEARCH_SESSION_KEY,
    JOB_STARTED_AT_KEY,
    SEARCH_START_LABEL_KEY,
)


def _pop_search_state_keys(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Сброс ключей состояния сценария поиска и метрик сессии."""
    for key in _SEARCH_STATE_KEYS:
        context.user_data.pop(key, None)


def _get_feedback_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура оценки подборки маршрутов (оценка и «Пропустить»)."""
    buttons = [
        [InlineKeyboardButton(label, callback_data=f"feedback:{rating}")]
        for rating, label in FEEDBACK_OPTIONS
    ]
    buttons.append([InlineKeyboardButton("Пропустить", callback_data="feedback:skip")])
    return InlineKeyboardMarkup(buttons)


def _get_location_request_content() -> tuple[str, ReplyKeyboardMarkup]:
    """Текст и клавиатура запроса точки старта (геолокация + «Назад»)."""
    text = (
        "Отправьте геолокацию кнопкой ниже (на телефоне), введите координаты или адрес текстом.\n\n"
        "Координаты: широта, долгота — например: 55.7558, 37.6173\n"
        "Адрес: например — Москва, Красная площадь 1\n\n"
        "В десктопной или веб-версии Telegram кнопка геолокации может не работать — тогда введите координаты или адрес текстом."
    )
    keyboard = [
        [KeyboardButton("Отправить геолокацию", request_location=True)],
        [KeyboardButton("Назад")],
    ]
    reply_markup = ReplyKeyboardMarkup(
        keyboard,
        one_time_keyboard=True,
        resize_keyboard=True,
    )
    return text, reply_markup


def _get_distance_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора дистанции (три кнопки + «Назад» и «В начало»)."""
    buttons = [
        [InlineKeyboardButton(label, callback_data=f"distance:{key}")]
        for key, label, _km in DISTANCE_OPTIONS
    ]
    buttons.append([
        InlineKeyboardButton("← Назад", callback_data="search_back:location"),
        InlineKeyboardButton("В начало", callback_data="search_back:start"),
    ])
    return InlineKeyboardMarkup(buttons)

# Regex для координат: lat, lon (разделитель запятая, точка с запятой или пробел)
COORDS_PATTERN = re.compile(r"^(-?\d+\.?\d*)\s*[,;\s]\s*(-?\d+\.?\d*)$")


def _parse_coords(text: str) -> tuple[float, float] | None:
    """Парсинг координат из строки. Возвращает (lat, lon) или None."""
    text = text.strip()
    match = COORDS_PATTERN.match(text)
    if not match:
        return None
    try:
        lat = float(match.group(1).replace(",", "."))
        lon = float(match.group(2).replace(",", "."))
    except ValueError:
        return None
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        return None
    return (lat, lon)


def _format_llm_routes_message(routes: list[dict]) -> tuple[str, InlineKeyboardMarkup]:
    """
    Текст сообщения со списком маршрутов от LLM: описание и ссылка на Яндекс.Карты на каждый вариант.
    routes: [{"name", "description", "coordinates"}, ...]
    """
    if not routes:
        return (
            "Маршруты не найдены. Попробуйте изменить точку старта или дистанцию.\n\n"
            "Нажмите «Найти маршрут» для нового поиска.",
            InlineKeyboardMarkup([]),
        )
    blocks = []
    for i, r in enumerate(routes):
        name = html.escape(str(r["name"]))
        desc = html.escape(str(r["description"]))
        url = build_yandex_route_link(r["coordinates"])
        url_esc = html.escape(url, quote=True)
        link_line = f'<a href="{url_esc}">Открыть в Яндекс.Картах</a>'
        blocks.append(f"<b>{i + 1}. {name}</b>\n{desc}\n{link_line}")
    text = (
        "Вот варианты маршрутов. Ниже у каждого варианта — ссылка на построение маршрута в Яндекс.Картах.\n\n"
        + "\n\n".join(blocks)
    )
    return text, InlineKeyboardMarkup([])


async def find_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Старт сценария поиска — запрос стартовой точки (геолокация, координаты или адрес)."""
    context.user_data[JOB_STARTED_AT_KEY] = time.perf_counter()
    context.user_data.pop(SEARCH_START_LABEL_KEY, None)
    text, reply_markup = _get_location_request_content()
    await update.message.reply_text(text, reply_markup=reply_markup)
    return LOCATION


async def location_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Приём геолокации от пользователя."""
    loc = update.message.location
    if not loc:
        return LOCATION
    context.user_data["search_start_lat"] = loc.latitude
    context.user_data["search_start_lon"] = loc.longitude
    context.user_data[SEARCH_START_LABEL_KEY] = (
        f"геолокация: {loc.latitude:.6f}, {loc.longitude:.6f}"
    )
    await update.message.reply_text(
        "Точка старта принята.\n\nВыберите дистанцию:",
        reply_markup=_get_distance_keyboard(),
    )
    return DISTANCE


async def location_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Приём координат или адреса из текста."""
    raw = update.message.text.strip()
    coords = _parse_coords(raw)
    if coords is not None:
        lat, lon = coords
        context.user_data["search_start_lat"] = lat
        context.user_data["search_start_lon"] = lon
        context.user_data[SEARCH_START_LABEL_KEY] = (
            f"координаты (ввод): {raw} → {lat:.6f}, {lon:.6f}"
        )
        await update.message.reply_text(
            "Точка старта принята.\n\nВыберите дистанцию:",
            reply_markup=_get_distance_keyboard(),
        )
        return DISTANCE

    if len(raw) < 3:
        text, reply_markup = _get_location_request_content()
        await update.message.reply_text(
            "Слишком короткий запрос. Введите координаты (широта, долгота) или полный адрес.\n"
            "На телефоне можно нажать «Отправить геолокацию».",
            reply_markup=reply_markup,
        )
        return LOCATION

    try:
        result = await geocode_to_lat_lon(raw)
    except GeocodeUnavailableError:
        logger.exception("Геокодирование недоступно для запроса")
        text, reply_markup = _get_location_request_content()
        await update.message.reply_text(
            "Сервис геокодирования временно недоступен. Попробуйте позже или введите координаты вручную.\n"
            "На телефоне можно нажать «Отправить геолокацию».",
            reply_markup=reply_markup,
        )
        return LOCATION

    if result is None:
        text, reply_markup = _get_location_request_content()
        await update.message.reply_text(
            "Адрес не найден. Уточните формулировку или введите координаты: широта, долгота "
            "(например: 55.7558, 37.6173).\n"
            "На телефоне можно нажать «Отправить геолокацию».",
            reply_markup=reply_markup,
        )
        return LOCATION

    context.user_data["search_start_lat"] = result.lat
    context.user_data["search_start_lon"] = result.lon
    context.user_data[SEARCH_START_LABEL_KEY] = (
        f"адрес: {raw} → {result.display_name} ({result.lat:.6f}, {result.lon:.6f})"
    )
    await update.message.reply_text(
        f"Точка старта: {result.display_name}\n\nВыберите дистанцию:",
        reply_markup=_get_distance_keyboard(),
    )
    return DISTANCE


async def distance_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработка выбора дистанции по кнопке — вызов LLM и вывод маршрутов с кнопками."""
    query = update.callback_query
    if not query:
        return ConversationHandler.END
    await query.answer()

    if not query.data or not query.data.startswith("distance:"):
        return ConversationHandler.END

    key = query.data.replace("distance:", "").strip()
    distance = DISTANCE_KM_BY_KEY.get(key)
    if distance is None:
        await query.edit_message_text("Неизвестный вариант дистанции. Нажмите «Найти маршрут» для нового поиска.")
        return ConversationHandler.END

    context.user_data["search_distance"] = distance
    start_lat = context.user_data.get("search_start_lat")
    start_lon = context.user_data.get("search_start_lon")

    if start_lon is None or start_lat is None:
        await query.edit_message_text("Сессия поиска истекла. Нажмите «Найти маршрут» для нового поиска.")
        return ConversationHandler.END

    try:
        await query.edit_message_text(
            _DISTANCE_LOADING_TEXT,
            reply_markup=InlineKeyboardMarkup([]),
        )
    except BadRequest as e:
        # «message is not modified» и др. — всё равно ждём LLM и рисуем результат
        logger.debug("Не удалось показать загрузку: %s", e)

    routes: list[dict] | None = None
    llm_raw: str | None = None
    llm_prompt: str | None = None
    result_text = ""
    reply_markup: InlineKeyboardMarkup = InlineKeyboardMarkup([])
    try:
        routes, llm_raw, llm_prompt = await asyncio.to_thread(
            get_routes_from_llm,
            start_lat,
            start_lon,
            distance,
        )
        result_text, reply_markup = _format_llm_routes_message(routes)
    except LLMRouteServiceError as e:
        result_text = str(e) + "\n\nНажмите «Найти маршрут» для нового поиска."
        reply_markup = InlineKeyboardMarkup([])
    except Exception as e:
        logger.exception("Ошибка поиска маршрутов: %s", e)
        result_text = (
            "Произошла ошибка при поиске. Попробуйте изменить параметры "
            "или повторить позже.\n\n"
            "Нажмите «Найти маршрут» для нового поиска."
        )
        reply_markup = InlineKeyboardMarkup([])

    if routes is not None:
        settings = Settings()
        user = update.effective_user
        started = context.user_data.get(JOB_STARTED_AT_KEY)
        duration_sec = None
        if started is not None:
            duration_sec = time.perf_counter() - started
        start_label = context.user_data.get(SEARCH_START_LABEL_KEY) or "—"
        route_names = [r["name"] for r in routes]
        if user:
            await log_job_completed(
                context.bot,
                analytics_chat_id=settings.analytics_chat_id,
                telegram_user_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name,
                start_label=start_label,
                route_names=route_names,
                duration_seconds=duration_sec,
            )
            await log_llm_response(
                context.bot,
                analytics_chat_id=settings.analytics_chat_id,
                telegram_user_id=user.id,
                prompt_text=llm_prompt or "",
                raw_content=llm_raw or "",
                model_name=settings.openrouter_model,
            )

    await query.edit_message_text(
        result_text,
        parse_mode="HTML",
        disable_web_page_preview=True,
        reply_markup=reply_markup,
    )

    if routes is not None:
        context.user_data[FEEDBACK_SEARCH_SESSION_KEY] = True
        await query.message.reply_text(
            "Как вам подбор маршрутов?",
            reply_markup=_get_feedback_keyboard(),
        )

    context.user_data.pop("search_start_lon", None)
    context.user_data.pop("search_start_lat", None)
    context.user_data.pop(JOB_STARTED_AT_KEY, None)
    context.user_data.pop(SEARCH_START_LABEL_KEY, None)
    # search_distance не удаляем — нужен для insert_feedback после ответа на опрос

    return ConversationHandler.END


async def cancel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отмена текущего диалога поиска."""
    _pop_search_state_keys(context)
    await update.message.reply_text("Поиск отменён. Нажмите «Найти маршрут» для нового поиска.")
    return ConversationHandler.END


async def main_button_fallback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Кнопка «Главная» — выход в главное меню."""
    _pop_search_state_keys(context)
    await start_handler(update, context)
    return ConversationHandler.END


async def feedback_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка оценки подборки маршрутов или «Пропустить»."""
    query = update.callback_query
    if not query or not query.data or not query.data.startswith("feedback:"):
        return
    await query.answer()

    suffix = query.data.replace("feedback:", "").strip()
    if suffix == "skip":
        context.user_data.pop(FEEDBACK_SEARCH_SESSION_KEY, None)
        context.user_data.pop("search_distance", None)
        await query.edit_message_text("Ок, удачных пробежек!")
        return

    try:
        rating = int(suffix)
    except ValueError:
        context.user_data.pop(FEEDBACK_SEARCH_SESSION_KEY, None)
        context.user_data.pop("search_distance", None)
        await query.edit_message_text("Спасибо!")
        return

    was_search_feedback = context.user_data.pop(FEEDBACK_SEARCH_SESSION_KEY, None)
    distance_km = context.user_data.pop("search_distance", None) if was_search_feedback else None

    user_id = update.effective_user.id if update.effective_user else None
    if user_id and was_search_feedback:
        await asyncio.to_thread(
            insert_feedback,
            user_id,
            FEEDBACK_SEARCH_ROUTE_NAME,
            rating,
            None,
            distance_km,
        )
    await query.edit_message_text("Спасибо за отзыв!")


async def search_back_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработка «Назад» / «В начало» на шаге DISTANCE."""
    query = update.callback_query
    if not query or not query.data or not query.data.startswith("search_back:"):
        return ConversationHandler.END
    await query.answer()

    suffix = query.data.replace("search_back:", "").strip()
    if suffix == "start":
        _pop_search_state_keys(context)
        await query.message.reply_text(
            get_start_message(update.effective_user),
            reply_markup=get_main_keyboard(),
        )
        return ConversationHandler.END
    if suffix == "location":
        text, reply_markup = _get_location_request_content()
        await query.message.reply_text(text, reply_markup=reply_markup)
        return LOCATION
    return ConversationHandler.END


async def _back_to_start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Кнопка «Назад» на шаге LOCATION — выход в главное меню."""
    _pop_search_state_keys(context)
    await start_handler(update, context)
    return ConversationHandler.END


def get_search_conversation_handler() -> ConversationHandler:
    """Создать ConversationHandler для поиска маршрутов."""
    # Кнопка «Найти маршрут»: точное совпадение или подстрока (на случай отличий в клиенте)
    return ConversationHandler(
        entry_points=[
            CommandHandler("find", find_handler),
            MessageHandler(
                filters.TEXT
                & (filters.Regex(f"^{re.escape(BUTTON_FIND)}$") | filters.Regex("Найти маршрут")),
                find_handler,
            ),
        ],
        states={
            LOCATION: [
                MessageHandler(filters.Regex("^Назад$"), _back_to_start_handler),
                MessageHandler(filters.LOCATION, location_handler),
                MessageHandler(filters.TEXT & ~filters.COMMAND, location_text_handler),
            ],
            DISTANCE: [
                CallbackQueryHandler(distance_callback, pattern=r"^distance:"),
                CallbackQueryHandler(search_back_callback, pattern=r"^search_back:"),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_handler),
            MessageHandler(filters.Regex(f"^{re.escape(BUTTON_MAIN)}$"), main_button_fallback),
            MessageHandler(filters.Regex(f"^{re.escape(BUTTON_CANCEL)}$"), cancel_handler),
        ],
    )
