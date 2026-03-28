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

        # OpenRouter (поиск маршрутов через LLM; OpenAI-совместимый API)
        self.openrouter_api_key: Optional[str] = os.getenv("OPENROUTER_API_KEY")
        _orb = (os.getenv("OPENROUTER_BASE_URL") or "").strip()
        self.openrouter_base_url: str = _orb or "https://openrouter.ai/api/v1"
        self.openrouter_model: str = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")
        self.openrouter_app_title: str = os.getenv("OPENROUTER_APP_TITLE", "Project Unicorn")
        self.openrouter_http_referer: Optional[str] = os.getenv("OPENROUTER_HTTP_REFERER")
        _default_prompt = _project_root() / "config" / "prompts" / "route_search.txt"
        self.route_prompt_path: str = os.getenv("ROUTE_PROMPT_PATH", str(_default_prompt))

        # Supabase (пользователи и обратная связь)
        self.supabase_url: Optional[str] = os.getenv("SUPABASE_URL")
        self.supabase_service_key: Optional[str] = os.getenv("SUPABASE_SERVICE_KEY")

        # Геокодирование адреса старта (Яндекс при ключе, иначе Nominatim)
        self.yandex_geocoder_api_key: Optional[str] = os.getenv("YANDEX_GEOCODER_API_KEY")
        self.geocoder_user_agent: str = os.getenv(
            "GEOCODER_USER_AGENT",
            "ProjectUnicornBot/1.0",
        )

        # Логи завершения сценария поиска в отдельный Telegram-чат (опционально)
        _acid = (os.getenv("ANALYTICS_CHAT_ID") or "").strip()
        self.analytics_chat_id: Optional[str] = _acid or None

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
