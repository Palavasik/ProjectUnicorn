"""
Настройки приложения.
Загрузка и управление конфигурацией.
"""

import os
from typing import Optional


class Settings:
    """Класс для управления настройками приложения."""
    
    def __init__(self):
        """Инициализация настроек из переменных окружения."""
        self.bot_token: Optional[str] = os.getenv("BOT_TOKEN")
        self.debug: bool = os.getenv("DEBUG", "False").lower() == "true"
        self.log_level: str = os.getenv("LOG_LEVEL", "INFO")
        
        # Database settings
        self.database_url: Optional[str] = os.getenv("DATABASE_URL")
        
        # Redis settings (опционально)
        self.redis_host: Optional[str] = os.getenv("REDIS_HOST")
        self.redis_port: int = int(os.getenv("REDIS_PORT", "6379"))
        self.redis_db: int = int(os.getenv("REDIS_DB", "0"))

        # OpenRouteService (маршрутизация)
        self.ors_api_key: Optional[str] = os.getenv("OPENROUTESERVICE_API_KEY")

        # Railway / webhook
        self.port: int = int(os.getenv("PORT", "0"))
        self.webhook_url: Optional[str] = os.getenv("WEBHOOK_URL")
    
    def validate(self) -> bool:
        """
        Валидация обязательных настроек.
        
        Returns:
            True если все обязательные настройки присутствуют
        """
        if not self.bot_token:
            return False
        return True
