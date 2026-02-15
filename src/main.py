"""
Главный файл приложения Telegram-бота.
Точка входа для запуска бота.
"""

import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application

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


def main():
    """Основная функция запуска бота."""
    settings = Settings()

    if not settings.bot_token:
        logger.error("BOT_TOKEN не найден в переменных окружения!")
        return

    application = Application.builder().token(settings.bot_token).build()
    bot = Bot(application)
    bot.setup_handlers()

    logger.info("Бот запущен...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
