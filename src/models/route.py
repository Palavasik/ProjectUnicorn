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
