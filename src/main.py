"""
Главный файл приложения Telegram-бота.
Точка входа для запуска бота.
"""

import asyncio
import logging
import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

from bot.bot import Bot
from config.settings import Settings

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def main():
    """Основная функция запуска бота."""
    # Загрузка настроек
    settings = Settings()
    
    if not settings.bot_token:
        logger.error("BOT_TOKEN не найден в переменных окружения!")
        return
    
    # Создание приложения
    application = Application.builder().token(settings.bot_token).build()
    
    # Инициализация бота
    bot = Bot(application)
    bot.setup_handlers()
    
    # Запуск бота
    logger.info("Бот запущен...")
    await application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    asyncio.run(main())
