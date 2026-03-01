"""
Сервис для работы с маршрутами для бега.
Загрузка маршрутов из JSON (fallback). Поиск маршрутов — через LLM (см. llm_route_service).
"""

import json
import logging
from pathlib import Path
from typing import Optional

from models.route import Route

logger = logging.getLogger(__name__)

# Путь к файлу маршрутов относительно корня проекта
ROUTES_FILE = Path(__file__).resolve().parent.parent.parent / "data" / "routes.json"

# Типы поверхности (для совместимости)
SURFACE_TYPES = {
    "asphalt": "Асфальт",
    "park": "Парк",
    "trail": "Трейл",
    "embankment": "Набережная",
}

CITIES = ["Москва", "Санкт-Петербург"]


class RouteService:
    """Сервис для загрузки маршрутов из JSON."""

    def __init__(self, routes_file: Optional[Path] = None):
        self.routes_file = routes_file or ROUTES_FILE
        self._routes: list[Route] = []

    def load_routes(self) -> list[Route]:
        """Загрузить маршруты из JSON-файла."""
        if self._routes:
            return self._routes

        if not self.routes_file.exists():
            logger.warning("Файл маршрутов не найден: %s", self.routes_file)
            return []

        try:
            with open(self.routes_file, encoding="utf-8") as f:
                data = json.load(f)
            self._routes = [Route.from_dict(item) for item in data]
            logger.info("Загружено %d маршрутов из JSON", len(self._routes))
            return self._routes
        except (json.JSONDecodeError, KeyError) as e:
            logger.error("Ошибка загрузки маршрутов: %s", e)
            return []

    def get_cities(self) -> list[str]:
        """Получить список доступных городов."""
        return CITIES.copy()

    def get_surface_types(self) -> dict[str, str]:
        """Получить словарь типов поверхности (id -> label)."""
        return SURFACE_TYPES.copy()


route_service = RouteService()
