"""
Обработчики команд бота.
"""

from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import ContextTypes

# Текст кнопок (используется в клавиатуре и в обработчиках)
BUTTON_MAIN = "🏠 Главная"
BUTTON_FIND = "🔍 Найти маршрут"


def get_main_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура с основными кнопками вместо слэш-команд."""
    return ReplyKeyboardMarkup(
        [[BUTTON_MAIN, BUTTON_FIND]],
        resize_keyboard=True,
        is_persistent=True,
    )


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик команды /start и кнопки «Главная».

    Args:
        update: Объект Update от Telegram
        context: Контекст бота
    """
    user = update.effective_user
    welcome_message = (
        f"Привет, {user.first_name}!\n\n"
        "Я Project Unicorn — помогу найти место для бега в незнакомом городе.\n\n"
        "Быстро подберу маршрут под дистанцию и тип поверхности "
        "(парк, набережная, трейл, асфальт).\n\n"
        "Нажмите кнопку ниже, чтобы начать поиск."
    )
    await update.message.reply_text(
        welcome_message,
        reply_markup=get_main_keyboard(),
    )


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик команды /help.

    Args:
        update: Объект Update от Telegram
        context: Контекст бота
    """
    help_text = (
        "📚 Кнопки и команды:\n\n"
        "🏠 Главная — начать работу с ботом\n"
        "🔍 Найти маршрут — подбор маршрута (точка старта, дистанция, тип поверхности)\n\n"
        "Команды: /start, /find, /cancel, /help"
    )
    await update.message.reply_text(help_text)
