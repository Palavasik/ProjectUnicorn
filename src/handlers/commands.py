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
        f"Привет, {user.first_name}! 👋\n\n"
        "Добро пожаловать в Project Unicorn!\n"
        "Используйте /help для просмотра доступных команд."
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
        "📚 Доступные команды:\n\n"
        "/start - Начать работу с ботом\n"
        "/help - Показать это сообщение\n\n"
        "Для получения дополнительной информации обратитесь к документации."
    )
    
    await update.message.reply_text(help_text)
