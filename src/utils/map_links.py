"""
Утилиты для построения ссылок на карты.
"""

import json
from urllib.parse import quote


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
