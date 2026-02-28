"""
Главный файл приложения Telegram-бота.
Точка входа для запуска бота.
Локально: polling. На Railway: webhook.
"""

import asyncio
import logging
import os
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

    port = int(os.getenv("PORT", "0"))
    webhook_url = os.getenv("WEBHOOK_URL")

    if port and webhook_url:
        logger.info("Запуск в режиме webhook (Railway)...")
        application.run_webhook(
            listen="0.0.0.0",
            port=port,
            url_path="webhook",
            webhook_url=f"{webhook_url.rstrip('/')}/webhook",
            allowed_updates=Update.ALL_TYPES,
        )
    else:
        # Локальный polling: снимаем webhook, чтобы не было конфликта с Railway
        async def drop_webhook():
            await application.bot.delete_webhook(drop_pending_updates=True)
            logger.info("Webhook снят, обновления будут приходить через polling.")

        asyncio.run(drop_webhook())
        logger.info("Бот запущен (polling)...")
        application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
