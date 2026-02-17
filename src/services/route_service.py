"""
Сервис для работы с маршрутами для бега.
Поддерживает OpenRouteService (при наличии API-ключа) и fallback на JSON.
"""

import json
import logging
from pathlib import Path
from typing import Optional

from config.settings import Settings
from models.route import Route

from services.openroute_service import OpenRouteService

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

# Города для выбора (кнопки)
CITIES = ["Москва", "Санкт-Петербург"]

# Порог доли нужного surface для принятия маршрута (0.6 = 60%)
SURFACE_MATCH_THRESHOLD = 0.5


class RouteService:
    """Сервис для загрузки и фильтрации маршрутов."""

    def __init__(
        self,
        routes_file: Optional[Path] = None,
        ors_api_key: Optional[str] = None,
    ):
        self.routes_file = routes_file or ROUTES_FILE
        self._routes: list[Route] = []
        self.ors_api_key = ors_api_key
        self._ors_client: Optional[OpenRouteService] = None

    def _get_ors_client(self) -> Optional[OpenRouteService]:
        """Ленивая инициализация клиента ORS."""
        if self._ors_client is None and self.ors_api_key:
            self._ors_client = OpenRouteService(self.ors_api_key)
        return self._ors_client

    def load_routes(self) -> list[Route]:
        """Загрузить маршруты из JSON-файла (fallback)."""
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

    def search_ors(
        self,
        city: str,
        distance_km: float,
        surface_type: str,
    ) -> list[Route]:
        """Поиск маршрутов через OpenRouteService."""
        ors = self._get_ors_client()
        if not ors:
            return []

        coords = ors.geocode(city)
        if not coords:
            logger.warning("ORS: не удалось геокодировать %s", city)
            return []

        lon, lat = coords
        directions_order = ["north", "east", "south", "west"]
        best_routes: list[tuple[float, Route]] = []

        for direction in directions_order:
            route_data = ors.get_round_route(lon, lat, distance_km, direction)
            if not route_data:
                continue

            surface_share = ors.parse_surface_from_route(route_data)
            match_ratio = surface_share.get(surface_type, 0.0)

            if match_ratio >= SURFACE_MATCH_THRESHOLD:
                route = Route.from_ors(route_data, city, surface_type, direction)
                best_routes.append((match_ratio, route))

        if not best_routes:
            # Вернуть лучший по surface даже если ниже порога
            for direction in directions_order:
                route_data = ors.get_round_route(lon, lat, distance_km, direction)
                if route_data:
                    surface_share = ors.parse_surface_from_route(route_data)
                    match_ratio = surface_share.get(surface_type, 0.0)
                    route = Route.from_ors(route_data, city, surface_type, direction)
                    best_routes.append((match_ratio, route))
                    break

        best_routes.sort(key=lambda x: -x[0])
        return [r for _, r in best_routes[:3]]

    def search(
        self,
        city: str,
        distance_km: float,
        surface_type: str,
        tolerance_km: float = 2.0,
    ) -> list[Route]:
        """
        Поиск маршрутов по критериям.

        При наличии OPENROUTESERVICE_API_KEY использует ORS, иначе — JSON.
        """
        if self._get_ors_client():
            try:
                routes = self.search_ors(city, distance_km, surface_type)
                if routes:
                    logger.info("ORS: найдено %d маршрутов для %s", len(routes), city)
                    return routes
            except Exception as e:
                logger.error("ORS search error: %s, fallback to JSON", e)

        # Fallback на JSON
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
        return CITIES.copy()

    def get_surface_types(self) -> dict[str, str]:
        """Получить словарь типов поверхности (id -> label)."""
        return SURFACE_TYPES.copy()


# Синглтон с настройками из окружения
def _create_route_service() -> RouteService:
    settings = Settings()
    return RouteService(ors_api_key=settings.ors_api_key)


route_service = _create_route_service()
