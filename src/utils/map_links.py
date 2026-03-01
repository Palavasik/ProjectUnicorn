"""
Утилиты для построения ссылок на карты.
"""

import json
from urllib.parse import quote


def build_yandex_route_link(
    coordinates: list[list[float]],
    max_points: int = 25,
) -> str:
    """
    Ссылка на Яндекс.Карты для построения маршрута по точкам.

    Args:
        coordinates: [[lat, lon], ...] (широта, долгота — порядок для rtext)
        max_points: Максимум точек (прореживание при превышении, чтобы не превысить длину URL)

    Returns:
        URL вида https://yandex.ru/maps/?rtext=lat1,lon1~lat2,lon2~...
    """
    if not coordinates:
        return "https://yandex.ru/maps/"
    if len(coordinates) > max_points:
        step = len(coordinates) / max_points
        indices = [min(int(i * step), len(coordinates) - 1) for i in range(max_points)]
        coordinates = [coordinates[i] for i in indices]
    rtext = "~".join(f"{lat},{lon}" for lat, lon in coordinates)
    return f"https://yandex.ru/maps/?rtext={quote(rtext, safe=',~')}"


def build_route_map_link(
    coordinates: list[list[float]],
    max_points: int = 30,
) -> str:
    """
    Ссылка на geojson.io с отображением маршрута.

    Args:
        coordinates: [[lon, lat], ...] (GeoJSON order)
        max_points: Максимум точек (прореживание при превышении)

    Returns:
        URL для geojson.io с маршрутом
    """
    if not coordinates:
        return "https://www.openstreetmap.org/"

    if len(coordinates) > max_points:
        step = len(coordinates) / max_points
        indices = [min(int(i * step), len(coordinates) - 1) for i in range(max_points)]
        coordinates = [coordinates[i] for i in indices]

    geojson = {
        "type": "Feature",
        "properties": {},
        "geometry": {"type": "LineString", "coordinates": coordinates},
    }
    encoded = quote(json.dumps(geojson), safe="")
    return f"https://geojson.io/#data=data:application/json,{encoded}"
