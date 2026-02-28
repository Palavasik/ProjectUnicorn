"""
Модель маршрута для бега.
"""

from dataclasses import dataclass
from typing import Optional

from utils.map_links import build_route_map_link


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

        direction_labels = {
            "north": "север", "east": "восток", "south": "юг", "west": "запад",
            "north_east": "северо-восток", "south_east": "юго-восток",
            "south_west": "юго-запад", "north_west": "северо-запад",
            "north_north_east": "север-северо-восток", "east_south_east": "восток-юго-восток",
        }
        dir_label = direction_labels.get(direction, direction.replace("_", "-"))

        name = f"Маршрут от старта ({distance_km} км)"
        if dir_label:
            name = f"Маршрут на {dir_label} ({distance_km} км)"

        description = f"Круговой маршрут от стартовой точки. Дистанция {distance_km} км."
        features = [surface_type, "динамический маршрут"]

        geometry = route_data.get("geometry", {}).get("coordinates", [])
        map_link = build_route_map_link(geometry) if geometry else None

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
