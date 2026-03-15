"""
Обработчики команд бота.
"""

from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import ContextTypes

from services.supabase_client import upsert_user

# Текст кнопок (используется в клавиатуре и в обработчиках)
BUTTON_MAIN = "🏠 Главная"
BUTTON_FIND = "🔍 Найти маршрут"
BUTTON_HELP = "❓ Помощь"
BUTTON_CANCEL = "Отмена"


def get_main_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура с основными кнопками вместо слэш-команд."""
    return ReplyKeyboardMarkup(
        [
            [BUTTON_MAIN, BUTTON_FIND],
            [BUTTON_HELP, BUTTON_CANCEL],
        ],
        resize_keyboard=True,
        is_persistent=True,
    )


def get_start_message(user) -> str:
    """Текст приветствия для главного меню (для start_handler и callback «В начало»)."""
    return (
        f"Привет, {user.first_name}!\n\n"
        "Я Project Unicorn — помогу найти место для бега в незнакомом городе.\n\n"
        "Быстро подберу маршруты под дистанцию от вашей точки. "
        "(парк, набережная, трейл, асфальт).\n\n"
        "Нажмите кнопку ниже, чтобы начать поиск."
    )


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик команды /start и кнопки «Главная».

    Args:
        update: Объект Update от Telegram
        context: Контекст бота
    """
    user = update.effective_user
    await update.message.reply_text(
        get_start_message(user),
        reply_markup=get_main_keyboard(),
    )
    # Сохранение/обновление пользователя в Supabase (после ответа, без блокировки)
    upsert_user(
        telegram_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
    )


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик команды /help.

    Args:
        update: Объект Update от Telegram
        context: Контекст бота
    """
    help_text = (
        "📚 Кнопки:\n\n"
        "🏠 Главная — начать работу с ботом\n"
        "🔍 Найти маршрут — точка старта и дистанция; выдаётся до 10 вариантов с указанием типа поверхности у каждого\n"
        "❓ Помощь — эта справка\n"
        "Отмена — отменить поиск или вернуться на главную\n\n"
        "Команды /start, /find, /help, /cancel тоже работают."
    )
    await update.message.reply_text(help_text)
