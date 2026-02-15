"""
Обработчики обычных сообщений (не команд).
"""

from telegram import Update
from telegram.ext import ContextTypes


async def fallback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик неизвестных сообщений.

    Args:
        update: Объект Update от Telegram
        context: Контекст бота
    """
    await update.message.reply_text(
        "Не понимаю эту команду. Используйте /help для списка доступных команд."
    )
