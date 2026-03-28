"""
Обработчики поиска маршрутов для бега.
"""

import asyncio
import logging
import re

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    Update,
)
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from handlers.commands import (
    BUTTON_CANCEL,
    BUTTON_FIND,
    BUTTON_MAIN,
    get_main_keyboard,
    get_start_message,
    start_handler,
)
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

# Обратная связь после выбора маршрута: (оценка, подпись кнопки)
FEEDBACK_OPTIONS = [(5, "Отлично"), (3, "Норм"), (1, "Не зашло")]


def _get_feedback_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура оценки маршрута (оценка 1–5 и «Пропустить»)."""
    buttons = [
        [InlineKeyboardButton(label, callback_data=f"feedback:{rating}")]
        for rating, label in FEEDBACK_OPTIONS
    ]
    buttons.append([InlineKeyboardButton("Пропустить", callback_data="feedback:skip")])
    return InlineKeyboardMarkup(buttons)


def _get_location_request_content() -> tuple[str, ReplyKeyboardMarkup]:
    """Текст и клавиатура запроса точки старта (геолокация + «Назад»)."""
    text = (
        "Отправьте геолокацию кнопкой ниже (на телефоне) или введите координаты вручную: широта, долгота\n"
        "Например: 55.7558, 37.6173\n\n"
        "В десктопной или веб-версии Telegram кнопка может не работать — тогда введите координаты текстом."
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
    Текст сообщения со списком маршрутов от LLM и клавиатура с кнопкой выбора под каждым.
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
        blocks.append(f"<b>{i + 1}. {r['name']}</b>\n{r['description']}")
    text = "Вот варианты маршрутов. Нажмите кнопку под маршрутом, чтобы построить его в Яндекс.Картах.\n\n" + "\n\n".join(blocks)
    buttons = [
        [InlineKeyboardButton(f"Построить маршрут {i + 1} в Яндекс.Картах", callback_data=f"route_select:{i}")]
        for i in range(len(routes))
    ]
    return text, InlineKeyboardMarkup(buttons)


async def find_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Старт сценария поиска — запрос стартовой точки (геолокация или координаты)."""
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
    await update.message.reply_text(
        "Точка старта принята.\n\nВыберите дистанцию:",
        reply_markup=_get_distance_keyboard(),
    )
    return DISTANCE


async def location_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Приём координат из текста (lat, lon)."""
    text = update.message.text.strip()
    coords = _parse_coords(text)
    if coords is None:
        text, reply_markup = _get_location_request_content()
        await update.message.reply_text(
            "Неверный формат. Введите координаты: широта, долгота (например: 55.7558, 37.6173).\n"
            "На телефоне можно нажать «Отправить геолокацию».",
            reply_markup=reply_markup,
        )
        return LOCATION
    lat, lon = coords
    context.user_data["search_start_lat"] = lat
    context.user_data["search_start_lon"] = lon
    await update.message.reply_text(
        "Точка старта принята.\n\nВыберите дистанцию:",
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
        routes = await asyncio.to_thread(
            get_routes_from_llm,
            start_lat,
            start_lon,
            distance,
        )
        context.user_data["search_routes"] = routes
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

    await query.edit_message_text(
        result_text,
        parse_mode="HTML",
        disable_web_page_preview=True,
        reply_markup=reply_markup,
    )

    context.user_data.pop("search_start_lon", None)
    context.user_data.pop("search_start_lat", None)
    # search_distance не удаляем — понадобится для обратной связи после выбора маршрута

    return ConversationHandler.END


async def cancel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отмена текущего диалога поиска."""
    context.user_data.pop("search_start_lon", None)
    context.user_data.pop("search_start_lat", None)
    context.user_data.pop("search_distance", None)
    context.user_data.pop("search_routes", None)
    context.user_data.pop("feedback_route_name", None)
    context.user_data.pop("feedback_distance_km", None)
    await update.message.reply_text("Поиск отменён. Нажмите «Найти маршрут» для нового поиска.")
    return ConversationHandler.END


async def main_button_fallback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Кнопка «Главная» — выход в главное меню."""
    context.user_data.pop("search_start_lon", None)
    context.user_data.pop("search_start_lat", None)
    context.user_data.pop("search_distance", None)
    context.user_data.pop("search_routes", None)
    context.user_data.pop("feedback_route_name", None)
    context.user_data.pop("feedback_distance_km", None)
    await start_handler(update, context)
    return ConversationHandler.END


async def route_select_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка нажатия «Построить маршрут в Яндекс.Картах» — отправка ссылки по координатам."""
    query = update.callback_query
    if not query:
        return
    await query.answer()

    if not query.data or not query.data.startswith("route_select:"):
        return

    try:
        index = int(query.data.replace("route_select:", "").strip())
    except ValueError:
        return

    routes = context.user_data.get("search_routes")
    if not routes or index < 0 or index >= len(routes):
        await query.edit_message_text("Сессия истекла. Нажмите «Найти маршрут» для нового поиска.")
        context.user_data.pop("search_routes", None)
        return

    route = routes[index]
    url = build_yandex_route_link(route["coordinates"])
    await query.edit_message_text(
        f"<b>{route['name']}</b>\n\n"
        f"Построить маршрут в Яндекс.Картах:\n<a href=\"{url}\">Открыть маршрут</a>",
        parse_mode="HTML",
    )
    # Сохраняем данные для сбора обратной связи
    context.user_data["feedback_route_name"] = route["name"]
    context.user_data["feedback_distance_km"] = context.user_data.get("search_distance")
    context.user_data.pop("search_routes", None)
    # Запрос оценки
    await query.message.reply_text(
        "Как вам маршрут?",
        reply_markup=_get_feedback_keyboard(),
    )


async def feedback_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка нажатия кнопки оценки маршрута или «Пропустить»."""
    query = update.callback_query
    if not query or not query.data or not query.data.startswith("feedback:"):
        return
    await query.answer()

    route_name = context.user_data.pop("feedback_route_name", None)
    distance_km = context.user_data.pop("feedback_distance_km", None)
    context.user_data.pop("search_distance", None)

    suffix = query.data.replace("feedback:", "").strip()
    if suffix == "skip":
        await query.edit_message_text("Ок, удачных пробежек!")
        return

    try:
        rating = int(suffix)
    except ValueError:
        await query.edit_message_text("Спасибо!")
        return

    user_id = update.effective_user.id if update.effective_user else None
    if user_id and route_name:
        await asyncio.to_thread(
            insert_feedback,
            user_id,
            route_name,
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
        for key in ("search_start_lat", "search_start_lon", "search_distance", "search_routes", "feedback_route_name", "feedback_distance_km"):
            context.user_data.pop(key, None)
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
    for key in ("search_start_lat", "search_start_lon", "search_distance", "search_routes", "feedback_route_name", "feedback_distance_km"):
        context.user_data.pop(key, None)
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
