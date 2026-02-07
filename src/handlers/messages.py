"""
Обработчики обычных сообщений (не команд).
"""

from telegram import Update
from telegram.ext import ContextTypes


async def echo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик текстовых сообщений.
    Пример эхо-бота - возвращает то же сообщение.
    
    Args:
        update: Объект Update от Telegram
        context: Контекст бота
    """
    user_message = update.message.text
    
    # Здесь можно добавить логику обработки сообщений
    # Например, анализ текста, вызов сервисов и т.д.
    
    response = f"Вы написали: {user_message}"
    await update.message.reply_text(response)
