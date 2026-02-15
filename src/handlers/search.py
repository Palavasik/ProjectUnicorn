"""
Обработчики поиска маршрутов для бега.
"""

import logging
import re

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

# Состояния диалога
CITY, DISTANCE, SURFACE = range(3)


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
            "другой город, дистанцию или тип поверхности.\n\n"
            "Используйте /find для нового поиска."
        )

    header = f"Нашёл {len(routes)} маршрут(ов) под ваши критерии:\n\n"
    items = [_format_route(r, i + 1) for i, r in enumerate(routes)]
    return header + "\n\n".join(items)


async def find_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Старт сценария поиска — показ выбора города."""
    cities = route_service.get_cities()
    keyboard = [
        [InlineKeyboardButton(city, callback_data=f"city:{city}")] for city in cities
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "Выберите город:",
        reply_markup=reply_markup,
    )
    return CITY


async def city_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработка выбора города."""
    query = update.callback_query
    await query.answer()

    if not query.data or not query.data.startswith("city:"):
        return ConversationHandler.END

    city = query.data.replace("city:", "")
    context.user_data["search_city"] = city

    await query.edit_message_text(f"Город: <b>{city}</b>\n\nУкажите желаемую дистанцию в км (например: 10):")
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
    city = context.user_data.get("search_city")
    distance = context.user_data.get("search_distance")

    if not city or not distance:
        await query.edit_message_text("Сессия поиска истекла. Используйте /find для нового поиска.")
        return ConversationHandler.END

    routes = route_service.search(city=city, distance_km=distance, surface_type=surface_type)
    result_text = _format_routes_list(routes)

    await query.edit_message_text(
        result_text,
        parse_mode="HTML",
        disable_web_page_preview=True,
    )

    # Очистка данных поиска
    context.user_data.pop("search_city", None)
    context.user_data.pop("search_distance", None)

    return ConversationHandler.END


async def cancel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отмена текущего диалога поиска."""
    context.user_data.pop("search_city", None)
    context.user_data.pop("search_distance", None)
    await update.message.reply_text("Поиск отменён. Используйте /find когда будете готовы.")
    return ConversationHandler.END


def get_search_conversation_handler() -> ConversationHandler:
    """Создать ConversationHandler для поиска маршрутов."""
    return ConversationHandler(
        entry_points=[CommandHandler("find", find_handler)],
        states={
            CITY: [
                CallbackQueryHandler(city_callback, pattern=r"^city:"),
            ],
            DISTANCE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, distance_handler),
            ],
            SURFACE: [
                CallbackQueryHandler(surface_callback, pattern=r"^surface:"),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_handler)],
    )
