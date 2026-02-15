"""
Обработчики команд бота.
"""

from telegram import Update
from telegram.ext import ContextTypes


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик команды /start.

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
        "Используйте /find чтобы начать поиск."
    )
    await update.message.reply_text(welcome_message)


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик команды /help.

    Args:
        update: Объект Update от Telegram
        context: Контекст бота
    """
    help_text = (
        "📚 Команды:\n\n"
        "/start — Начать работу с ботом\n"
        "/find — Найти маршрут для бега (город, дистанция, тип поверхности)\n"
        "/cancel — Отменить текущий поиск\n"
        "/help — Показать это сообщение"
    )
    await update.message.reply_text(help_text)
