"""
Основной класс бота.
Отвечает за настройку и регистрацию обработчиков.
"""

from telegram.ext import Application, CommandHandler, MessageHandler, filters

from handlers.commands import start_handler, help_handler
from handlers.messages import echo_handler


class Bot:
    """Класс для управления ботом."""
    
    def __init__(self, application: Application):
        """
        Инициализация бота.
        
        Args:
            application: Экземпляр Telegram Application
        """
        self.application = application
    
    def setup_handlers(self):
        """Настройка всех обработчиков команд и сообщений."""
        # Регистрация обработчиков команд
        self.application.add_handler(CommandHandler("start", start_handler))
        self.application.add_handler(CommandHandler("help", help_handler))
        
        # Регистрация обработчиков сообщений
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, echo_handler)
        )
        
        # Здесь можно добавить другие обработчики:
        # - CallbackQueryHandler для inline кнопок
        # - MessageHandler для других типов сообщений (фото, документы и т.д.)
