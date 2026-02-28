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

# Максимум маршрутов в выдаче (без выбора поверхности — показываем тип у каждого)
MAX_ROUTES_IN_RESULT = 10


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

    def _dominant_surface(self, surface_share: dict[str, float]) -> str:
        """Тип поверхности с максимальной долей; по умолчанию asphalt."""
        if not surface_share:
            return "asphalt"
        return max(surface_share, key=surface_share.get)  # type: ignore[arg-type]

    def search_ors(
        self,
        start_lon: float,
        start_lat: float,
        distance_km: float,
    ) -> list[Route]:
        """
        Поиск маршрутов через OpenRouteService от заданной точки.
        Возвращает до MAX_ROUTES_IN_RESULT вариантов; у каждого свой тип поверхности из ORS.
        """
        ors = self._get_ors_client()
        if not ors:
            return []

        place_name = "От вашей точки"
        directions_order = list(ors.get_directions_order())
        routes: list[Route] = []

        for direction in directions_order:
            if len(routes) >= MAX_ROUTES_IN_RESULT:
                break
            route_data = ors.get_round_route(start_lon, start_lat, distance_km, direction)
            if not route_data:
                continue
            surface_share = ors.parse_surface_from_route(route_data)
            surface_type = self._dominant_surface(surface_share)
            route = Route.from_ors(route_data, place_name, surface_type, direction)
            routes.append(route)

        return routes

    def search(
        self,
        start_lon: float,
        start_lat: float,
        distance_km: float,
    ) -> list[Route]:
        """
        Поиск маршрутов по точке старта и дистанции.
        Возвращает до 10 вариантов; тип поверхности определяется по данным ORS для каждого маршрута.

        Требует OPENROUTESERVICE_API_KEY. Без ключа выбрасывает ValueError.
        """
        if not self._get_ors_client():
            raise ValueError(
                "Поиск по точке доступен только при настройке OpenRouteService. "
                "Укажите OPENROUTESERVICE_API_KEY в настройках."
            )
        routes = self.search_ors(start_lon, start_lat, distance_km)
        if routes:
            logger.info(
                "ORS: найдено %d маршрутов для (%.4f, %.4f)",
                len(routes),
                start_lon,
                start_lat,
            )
        return routes

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
