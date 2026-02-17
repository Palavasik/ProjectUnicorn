"""
Модель маршрута для бега.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Route:
    """Маршрут для бега в городе."""

    id: str
    city: str
    name: str
    distance_km: float
    surface_type: str  # asphalt, park, trail, embankment
    description: str
    features: list[str]
    map_link: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> "Route":
        """Создать Route из словаря (например, из JSON)."""
        return cls(
            id=data["id"],
            city=data["city"],
            name=data["name"],
            distance_km=float(data["distance_km"]),
            surface_type=data["surface_type"],
            description=data["description"],
            features=data.get("features", []),
            map_link=data.get("map_link"),
        )

    @classmethod
    def from_ors(
        cls,
        route_data: dict,
        city: str,
        surface_type: str,
        direction: str = "",
    ) -> "Route":
        """
        Создать Route из ответа OpenRouteService API.

        Args:
            route_data: Объект route из routes[0]
            city: Название города
            surface_type: Тип поверхности (asphalt, park, trail, embankment)
            direction: Направление маршрута (для name)
        """
        summary = route_data.get("summary", {})
        distance_m = summary.get("distance", 0)
        distance_km = round(distance_m / 1000, 1)

        direction_labels = {"north": "север", "east": "восток", "south": "юг", "west": "запад"}
        dir_label = direction_labels.get(direction, "")

        name = f"Маршрут от центра ({distance_km} км)"
        if dir_label:
            name = f"Маршрут на {dir_label} ({distance_km} км)"

        description = f"Круговой маршрут от центра города. Дистанция {distance_km} км."
        features = [surface_type, "динамический маршрут"]

        geometry = route_data.get("geometry", {}).get("coordinates", [])
        map_link = None
        if geometry:
            mid = len(geometry) // 2
            lat, lon = geometry[mid][1], geometry[mid][0]
            map_link = f"https://www.openstreetmap.org/?mlat={lat}&mlon={lon}&zoom=14"

        route_id = f"ors-{city}-{distance_km}-{surface_type}-{direction}".replace(" ", "_")

        return cls(
            id=route_id,
            city=city,
            name=name,
            distance_km=distance_km,
            surface_type=surface_type,
            description=description,
            features=features,
            map_link=map_link,
        )
