"""
Клиент OpenRouteService API.
Геокодинг и построение маршрутов для бега.
"""

import logging
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

ORS_BASE = "https://api.openrouteservice.org"
GEOCODE_URL = f"{ORS_BASE}/geocode/search"
DIRECTIONS_URL = f"{ORS_BASE}/v2/directions/foot-walking/geojson"

# ORS surface IDs: https://giscience.github.io/openrouteservice/api-reference/endpoints/directions/extra-info/surface/
# 0=Unknown, 1=Paved, 2=Unpaved, 3=Asphalt, 4=Concrete, 8=Compacted Gravel, 10=Gravel,
# 11=Dirt, 12=Ground, 14=Paving Stones, 17=Grass
ORS_SURFACE_ID_TO_PRODUCT = {
    0: "asphalt",
    1: "asphalt",
    2: "trail",
    3: "asphalt",
    4: "asphalt",
    6: "asphalt",
    7: "trail",
    8: "trail",
    10: "trail",
    11: "trail",
    12: "park",
    13: "trail",
    14: "embankment",
    15: "trail",
    17: "park",
    18: "park",
}

# Направления для построения кругового маршрута (delta lat, delta lon на 1 км)
# lat: 1 deg ≈ 111 km, lon: 1 deg ≈ 111*cos(lat) km
DIRECTIONS = {
    "north": (1 / 111, 0),
    "east": (0, 1 / (111 * 0.6)),  # cos(55°) ≈ 0.6 для Москвы
    "south": (-1 / 111, 0),
    "west": (0, -1 / (111 * 0.6)),
}


class OpenRouteServiceError(Exception):
    """Ошибка при обращении к OpenRouteService API."""

    pass


class OpenRouteService:
    """Клиент OpenRouteService API."""

    def __init__(self, api_key: str, timeout: float = 15.0):
        self.api_key = api_key
        self.timeout = timeout

    def geocode(self, text: str) -> Optional[tuple[float, float]]:
        """
        Геокодинг: название города -> (lon, lat).

        Args:
            text: Название города (например, "Москва")

        Returns:
            (longitude, latitude) или None при ошибке
        """
        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.get(
                    GEOCODE_URL,
                    params={"api_key": self.api_key, "text": text},
                )
                resp.raise_for_status()
                data = resp.json()

            features = data.get("features", [])
            if not features:
                logger.warning("Geocode: пустой ответ для %s", text)
                return None

            coords = features[0].get("geometry", {}).get("coordinates")
            if not coords or len(coords) < 2:
                return None

            lon, lat = float(coords[0]), float(coords[1])
            logger.info("Geocode %s -> (%.4f, %.4f)", text, lon, lat)
            return (lon, lat)

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                logger.error("ORS: превышен лимит запросов (429)")
            else:
                logger.error("ORS geocode error: %s", e)
            return None
        except (httpx.RequestError, KeyError, ValueError) as e:
            logger.error("ORS geocode error: %s", e)
            return None

    def _point_at_distance(
        self, lon: float, lat: float, distance_km: float, direction: str
    ) -> tuple[float, float]:
        """Точка в direction на distance_km от (lon, lat)."""
        dlat, dlon = DIRECTIONS.get(direction, DIRECTIONS["north"])
        half = distance_km / 2
        delta_lat = dlat * half
        delta_lon = dlon * half
        return (lon + delta_lon, lat + delta_lat)

    def get_round_route(
        self,
        lon: float,
        lat: float,
        distance_km: float,
        direction: str = "north",
    ) -> Optional[dict]:
        """
        Построить круговой маршрут: центр -> точка -> центр.

        Args:
            lon, lat: Координаты центра
            distance_km: Желаемая дистанция в км
            direction: Направление (north, east, south, west)

        Returns:
            Ответ ORS API (routes[0]) или None
        """
        mid_lon, mid_lat = self._point_at_distance(lon, lat, distance_km, direction)
        coordinates = [[lon, lat], [mid_lon, mid_lat], [lon, lat]]

        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(
                    DIRECTIONS_URL,
                    params={"api_key": self.api_key},
                    json={
                        "coordinates": coordinates,
                        "extra_info": ["surface"],
                    },
                )
                resp.raise_for_status()
                data = resp.json()

            # GeoJSON: features; JSON: routes
            routes = data.get("features") or data.get("routes", [])
            if not routes:
                logger.warning("ORS: пустой список маршрутов")
                return None

            feat = routes[0]
            # GeoJSON: geometry + properties; JSON: flat
            if "geometry" in feat and "properties" in feat:
                props = feat["properties"]
                return {
                    "summary": props.get("summary", {}),
                    "extras": props.get("extras", {}),
                    "geometry": {"coordinates": feat["geometry"].get("coordinates", [])},
                }
            return feat

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                logger.error("ORS: превышен лимит запросов (429)")
            else:
                logger.error("ORS directions error: %s", e)
            return None
        except (httpx.RequestError, KeyError) as e:
            logger.error("ORS directions error: %s", e)
            return None

    def parse_surface_from_route(self, route: dict) -> dict[str, float]:
        """
        Доля каждого типа поверхности (продукт) по сегментам маршрута.

        ORS возвращает values: [[from_m, to_m, surface_id], ...]

        Returns:
            {"asphalt": 0.7, "park": 0.2, "trail": 0.1, ...}
        """
        result: dict[str, float] = {}
        segments = route.get("extras", {}).get("surface", {}).get("values", [])
        if not segments:
            return {"asphalt": 1.0}

        total_length = 0.0
        for seg in segments:
            if len(seg) >= 2:
                total_length += seg[1] - seg[0]

        length_by_product: dict[str, float] = {}
        for seg in segments:
            if len(seg) < 3:
                continue
            length = seg[1] - seg[0]
            surface_id = seg[2] if isinstance(seg[2], int) else 0
            product = ORS_SURFACE_ID_TO_PRODUCT.get(surface_id, "asphalt")
            length_by_product[product] = length_by_product.get(product, 0) + length

        if total_length <= 0:
            return {"asphalt": 1.0}

        for product, length in length_by_product.items():
            result[product] = length / total_length

        return result

    def build_map_link(self, geometry: list, center_lon: float = 0, center_lat: float = 0) -> str:
        """Ссылка на карту. ORS geometry: [[lon, lat], ...]."""
        if geometry and isinstance(geometry[0], (list, tuple)):
            coords = geometry
            if coords:
                lat = coords[len(coords) // 2][1]
                lon = coords[len(coords) // 2][0]
                return f"https://www.openstreetmap.org/?mlat={lat}&mlon={lon}&zoom=14"
        if center_lat and center_lon:
            return f"https://www.openstreetmap.org/?mlat={center_lat}&mlon={center_lon}&zoom=14"
        return "https://www.openstreetmap.org/"
