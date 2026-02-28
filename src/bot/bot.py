"""
Основной класс бота.
Отвечает за настройку и регистрацию обработчиков.
"""

import re
from telegram.ext import CommandHandler, MessageHandler, filters

from handlers.commands import (
    BUTTON_CANCEL,
    BUTTON_HELP,
    BUTTON_MAIN,
    help_handler,
    start_handler,
)
from handlers.messages import fallback_handler
from handlers.search import get_search_conversation_handler


class Bot:
    """Класс для управления ботом."""

    def __init__(self, application):
        """
        Инициализация бота.

        Args:
            application: Экземпляр Telegram Application
        """
        self.application = application

    def setup_handlers(self):
        """Настройка всех обработчиков команд и сообщений."""
        self.application.add_handler(CommandHandler("start", start_handler))
        self.application.add_handler(CommandHandler("help", help_handler))
        self.application.add_handler(get_search_conversation_handler())
        # Кнопки вместо слэш-команд
        self.application.add_handler(
            MessageHandler(
                filters.Regex(f"^{re.escape(BUTTON_MAIN)}$"),
                start_handler,
            )
        )
        self.application.add_handler(
            MessageHandler(
                filters.Regex(f"^{re.escape(BUTTON_HELP)}$"),
                help_handler,
            )
        )
        self.application.add_handler(
            MessageHandler(
                filters.Regex(f"^{re.escape(BUTTON_CANCEL)}$"),
                start_handler,
            )
        )
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, fallback_handler)
        )
