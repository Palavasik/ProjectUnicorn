# -*- coding: utf-8 -*-
"""
Application settings and configuration.
"""

import os
from pathlib import Path
from typing import Optional

from utils.database_url import normalize_database_url


def _project_root() -> Path:
    """Корень проекта (родитель каталога src)."""
    return Path(__file__).resolve().parent.parent.parent


class Settings:
    """Класс для управления настройками приложения."""

    def __init__(self):
        """Инициализация настроек из переменных окружения."""
        self.bot_token: Optional[str] = os.getenv("BOT_TOKEN")
        self.debug: bool = os.getenv("DEBUG", "False").lower() == "true"
        self.log_level: str = os.getenv("LOG_LEVEL", "INFO")

        # Database settings (IPv4 hostaddr для db.*.supabase.co на Railway без IPv6)
        self.database_url: Optional[str] = normalize_database_url(
            os.getenv("DATABASE_URL")
        )

        # Redis settings (опционально)
        self.redis_host: Optional[str] = os.getenv("REDIS_HOST")
        self.redis_port: int = int(os.getenv("REDIS_PORT", "6379"))
        self.redis_db: int = int(os.getenv("REDIS_DB", "0"))

        # OpenAI (поиск маршрутов через LLM)
        self.openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
        self.openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        _default_prompt = _project_root() / "config" / "prompts" / "route_search.txt"
        self.route_prompt_path: str = os.getenv("ROUTE_PROMPT_PATH", str(_default_prompt))

        # Supabase (пользователи и обратная связь)
        self.supabase_url: Optional[str] = os.getenv("SUPABASE_URL")
        self.supabase_service_key: Optional[str] = os.getenv("SUPABASE_SERVICE_KEY")

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
