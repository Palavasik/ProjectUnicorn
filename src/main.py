"""
Главный файл приложения Telegram-бота.
Точка входа для запуска бота.
Локально: polling. На Railway: webhook.
"""

import logging
import os
from dotenv import load_dotenv
import httpx
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


def _delete_webhook_sync(bot_token: str) -> None:
    """Синхронно снять webhook (чтобы не создавать event loop до run_polling)."""
    url = f"https://api.telegram.org/bot{bot_token}/deleteWebhook"
    try:
        with httpx.Client(timeout=10.0) as client:
            r = client.post(url, params={"drop_pending_updates": "true"})
            r.raise_for_status()
        logger.info("Webhook снят, обновления будут приходить через polling.")
    except Exception as e:
        logger.warning("Не удалось снять webhook: %s", e)


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
        # Локальный polling: снимаем webhook синхронно (без asyncio), чтобы не ломать event loop
        if not webhook_url and os.getenv("PORT"):
            logger.warning(
                "WEBHOOK_URL не задан при заданном PORT — запуск в режиме polling. "
                "Для работы на Railway добавьте переменную WEBHOOK_URL (публичный URL сервиса)."
            )
        _delete_webhook_sync(settings.bot_token)
        logger.info("Бот запущен (polling)...")
        application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
