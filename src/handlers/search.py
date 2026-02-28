"""
Обработчики поиска маршрутов для бега.
"""

import logging
import re

import httpx
from telegram import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from services.route_service import route_service

logger = logging.getLogger(__name__)

# Состояния диалога: стартовая точка -> дистанция -> поверхность
LOCATION, DISTANCE, SURFACE = range(3)

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


def _format_route(route, index: int) -> str:
    """Форматирование одного маршрута для вывода."""
    features = ", ".join(route.features) if route.features else "—"
    surface_label = route_service.get_surface_types().get(
        route.surface_type, route.surface_type
    )
    lines = [
        f"<b>{index}. {route.name}</b>",
        f"   📏 {route.distance_km} км | {surface_label}",
        f"   {route.description}",
        f"   Особенности: {features}",
    ]
    if route.map_link:
        lines.append(f"   🗺 <a href=\"{route.map_link}\">Открыть на карте</a>")
    return "\n".join(lines)


def _format_routes_list(routes: list) -> str:
    """Форматирование списка маршрутов."""
    if not routes:
        return (
            "Маршруты не найдены. Попробуйте изменить параметры: "
            "другую точку старта, дистанцию или тип поверхности.\n\n"
            "Используйте /find для нового поиска."
        )

    header = f"Нашёл {len(routes)} маршрут(ов) под ваши критерии:\n\n"
    items = [_format_route(r, i + 1) for i, r in enumerate(routes)]
    return header + "\n\n".join(items)


async def find_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Старт сценария поиска — запрос стартовой точки (геолокация или координаты)."""
    keyboard = [[KeyboardButton("Отправить геолокацию", request_location=True)]]
    reply_markup = ReplyKeyboardMarkup(
        keyboard,
        one_time_keyboard=True,
        resize_keyboard=True,
    )
    await update.message.reply_text(
        "Отправьте геолокацию (кнопка ниже) или введите координаты старта, например: 55.7558, 37.6173",
        reply_markup=reply_markup,
    )
    return LOCATION


async def location_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Приём геолокации от пользователя."""
    loc = update.message.location
    if not loc:
        return LOCATION
    context.user_data["search_start_lat"] = loc.latitude
    context.user_data["search_start_lon"] = loc.longitude
    await update.message.reply_text(
        "Точка старта принята.\n\nУкажите желаемую дистанцию в км (например: 10):",
        reply_markup=ReplyKeyboardRemove(),
    )
    return DISTANCE


async def location_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Приём координат из текста (lat, lon)."""
    text = update.message.text.strip()
    coords = _parse_coords(text)
    if coords is None:
        await update.message.reply_text(
            "Неверный формат. Введите координаты в формате: широта, долгота\n"
            "Например: 55.7558, 37.6173\n"
            "Или отправьте геолокацию кнопкой ниже.",
            reply_markup=ReplyKeyboardMarkup(
                [[KeyboardButton("Отправить геолокацию", request_location=True)]],
                one_time_keyboard=True,
                resize_keyboard=True,
            ),
        )
        return LOCATION
    lat, lon = coords
    context.user_data["search_start_lat"] = lat
    context.user_data["search_start_lon"] = lon
    await update.message.reply_text(
        "Точка старта принята.\n\nУкажите желаемую дистанцию в км (например: 10):",
        reply_markup=ReplyKeyboardRemove(),
    )
    return DISTANCE


async def distance_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Приём дистанции от пользователя."""
    text = update.message.text.strip()

    # Валидация: число от 1 до 50
    match = re.match(r"^(\d+(?:[.,]\d+)?)$", text.replace(",", "."))
    if not match:
        await update.message.reply_text(
            "Пожалуйста, введите число — дистанцию в километрах (например: 10 или 5.5):"
        )
        return DISTANCE

    try:
        distance = float(match.group(1).replace(",", "."))
    except ValueError:
        await update.message.reply_text("Введите корректное число (например: 10):")
        return DISTANCE

    if distance < 1 or distance > 50:
        await update.message.reply_text("Дистанция должна быть от 1 до 50 км:")
        return DISTANCE

    context.user_data["search_distance"] = distance

    surface_types = route_service.get_surface_types()
    keyboard = [
        [
            InlineKeyboardButton(label, callback_data=f"surface:{stype}")
            for stype, label in list(surface_types.items())[i : i + 2]
        ]
        for i in range(0, len(surface_types), 2)
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"Дистанция: <b>{distance} км</b>\n\nВыберите тип поверхности:",
        reply_markup=reply_markup,
    )
    return SURFACE


async def surface_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработка выбора типа поверхности — поиск и вывод результатов."""
    query = update.callback_query
    await query.answer()

    if not query.data or not query.data.startswith("surface:"):
        return ConversationHandler.END

    surface_type = query.data.replace("surface:", "")
    start_lon = context.user_data.get("search_start_lon")
    start_lat = context.user_data.get("search_start_lat")
    distance = context.user_data.get("search_distance")

    if start_lon is None or start_lat is None or distance is None:
        await query.edit_message_text("Сессия поиска истекла. Используйте /find для нового поиска.")
        return ConversationHandler.END

    try:
        routes = route_service.search(
            start_lon=start_lon,
            start_lat=start_lat,
            distance_km=distance,
            surface_type=surface_type,
        )
        result_text = _format_routes_list(routes)
    except ValueError as e:
        # Нет ORS ключа — сервис выбросит ValueError с сообщением
        result_text = str(e) + "\n\nИспользуйте /find для нового поиска."
    except httpx.TimeoutException:
        logger.warning("Timeout при поиске маршрутов для (%.4f, %.4f)", start_lon, start_lat)
        result_text = (
            "Сервис маршрутизации не ответил вовремя. "
            "Попробуйте позже или измените параметры поиска.\n\n"
            "Используйте /find для нового поиска."
        )
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 429:
            result_text = (
                "Превышен лимит запросов к сервису маршрутов. "
                "Попробуйте через несколько минут.\n\n"
                "Используйте /find для нового поиска."
            )
        else:
            result_text = (
                "Временная ошибка сервиса маршрутов. "
                "Попробуйте позже.\n\n"
                "Используйте /find для нового поиска."
            )
        logger.error("ORS HTTP error: %s", e)
    except Exception as e:
        logger.exception("Ошибка поиска маршрутов: %s", e)
        result_text = (
            "Произошла ошибка при поиске. Попробуйте изменить параметры "
            "или повторить позже.\n\n"
            "Используйте /find для нового поиска."
        )

    await query.edit_message_text(
        result_text,
        parse_mode="HTML",
        disable_web_page_preview=True,
    )

    # Очистка данных поиска
    context.user_data.pop("search_start_lon", None)
    context.user_data.pop("search_start_lat", None)
    context.user_data.pop("search_distance", None)

    return ConversationHandler.END


async def cancel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отмена текущего диалога поиска."""
    context.user_data.pop("search_start_lon", None)
    context.user_data.pop("search_start_lat", None)
    context.user_data.pop("search_distance", None)
    await update.message.reply_text("Поиск отменён. Используйте /find когда будете готовы.")
    return ConversationHandler.END


def get_search_conversation_handler() -> ConversationHandler:
    """Создать ConversationHandler для поиска маршрутов."""
    return ConversationHandler(
        entry_points=[CommandHandler("find", find_handler)],
        states={
            LOCATION: [
                MessageHandler(filters.LOCATION, location_handler),
                MessageHandler(filters.TEXT & ~filters.COMMAND, location_text_handler),
            ],
            DISTANCE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, distance_handler),
            ],
            SURFACE: [
                CallbackQueryHandler(surface_callback, pattern=r"^surface:"),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_handler)],
        per_message=True,
    )
