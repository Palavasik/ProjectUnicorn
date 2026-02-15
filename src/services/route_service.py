"""
Сервис для работы с маршрутами для бега.
"""

import json
import logging
from pathlib import Path
from typing import Optional

from models.route import Route

logger = logging.getLogger(__name__)

# Путь к файлу маршрутов относительно корня проекта
ROUTES_FILE = Path(__file__).resolve().parent.parent.parent / "data" / "routes.json"

# Типы поверхности
SURFACE_TYPES = {
    "asphalt": "Асфальт",
    "park": "Парк",
    "trail": "Трейл",
    "embankment": "Набережная",
}

# Города для MVP
CITIES = ["Москва", "Санкт-Петербург"]


class RouteService:
    """Сервис для загрузки и фильтрации маршрутов."""

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
            logger.info("Загружено %d маршрутов", len(self._routes))
            return self._routes
        except (json.JSONDecodeError, KeyError) as e:
            logger.error("Ошибка загрузки маршрутов: %s", e)
            return []

    def search(
        self,
        city: str,
        distance_km: float,
        surface_type: str,
        tolerance_km: float = 2.0,
    ) -> list[Route]:
        """
        Поиск маршрутов по критериям.

        Args:
            city: Город
            distance_km: Желаемая дистанция в км
            surface_type: Тип поверхности (asphalt, park, trail, embankment)
            tolerance_km: Допуск по дистанции (по умолчанию ±2 км)

        Returns:
            Список подходящих маршрутов
        """
        routes = self.load_routes()
        min_dist = distance_km - tolerance_km
        max_dist = distance_km + tolerance_km

        filtered = [
            r
            for r in routes
            if r.city == city
            and r.surface_type == surface_type
            and min_dist <= r.distance_km <= max_dist
        ]

        filtered.sort(key=lambda r: abs(r.distance_km - distance_km))
        return filtered

    def get_cities(self) -> list[str]:
        """Получить список доступных городов."""
        routes = self.load_routes()
        cities = sorted(set(r.city for r in routes))
        return cities if cities else CITIES

    def get_surface_types(self) -> dict[str, str]:
        """Получить словарь типов поверхности (id -> label)."""
        return SURFACE_TYPES.copy()


# Синглтон для использования в хендлерах
route_service = RouteService()
