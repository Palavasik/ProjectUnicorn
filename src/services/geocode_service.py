"""
Геокодирование адреса в координаты: Яндекс (если задан ключ) или Nominatim (OSM).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

import httpx

from config.settings import Settings

logger = logging.getLogger(__name__)

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
YANDEX_GEOCODE_URL = "https://geocode-maps.yandex.ru/1.x/"


class GeocodeUnavailableError(Exception):
    """Сеть, таймаут или ошибка HTTP при обращении к геокодеру."""

    pass


@dataclass(frozen=True)
class GeocodeResult:
    """Результат геокодирования: широта, долгота, подпись для пользователя."""

    lat: float
    lon: float
    display_name: str


async def _nominatim_geocode(
    client: httpx.AsyncClient,
    query: str,
    user_agent: str,
) -> Optional[GeocodeResult]:
    """Первый результат Nominatim или None, если пусто."""
    response = await client.get(
        NOMINATIM_URL,
        params={"q": query, "format": "json", "limit": "1"},
        headers={"User-Agent": user_agent},
    )
    response.raise_for_status()
    data = response.json()
    if not data:
        return None
    item = data[0]
    return GeocodeResult(
        lat=float(item["lat"]),
        lon=float(item["lon"]),
        display_name=str(item.get("display_name") or query),
    )


async def _yandex_geocode(
    client: httpx.AsyncClient,
    query: str,
    api_key: str,
) -> Optional[GeocodeResult]:
    """Первый результат Яндекс.Геокодера или None."""
    response = await client.get(
        YANDEX_GEOCODE_URL,
        params={
            "apikey": api_key,
            "geocode": query,
            "format": "json",
            "results": "1",
        },
    )
    response.raise_for_status()
    data = response.json()
    members = (
        data.get("response", {})
        .get("GeoObjectCollection", {})
        .get("featureMember", [])
    )
    if not members:
        return None
    geo = members[0].get("GeoObject") or {}
    pos = (geo.get("Point") or {}).get("pos", "")
    parts = str(pos).split()
    if len(parts) != 2:
        return None
    lon_f, lat_f = float(parts[0]), float(parts[1])
    name = str(geo.get("name") or query)
    desc = str(geo.get("description") or "").strip()
    display = f"{name}, {desc}" if desc else name
    return GeocodeResult(lat=lat_f, lon=lon_f, display_name=display.strip())


async def geocode_to_lat_lon(
    query: str,
    settings: Optional[Settings] = None,
) -> Optional[GeocodeResult]:
    """
    Преобразовать текстовый адрес в координаты.

    При заданном YANDEX_GEOCODER_API_KEY используется Яндекс, иначе Nominatim.

    Args:
        query: Строка запроса (адрес, название места).
        settings: Настройки; если None, создаётся новый экземпляр Settings.

    Returns:
        GeocodeResult или None, если точек не найдено.

    Raises:
        GeocodeUnavailableError: при сетевой или HTTP-ошибке.
    """
    cfg = settings or Settings()
    timeout = httpx.Timeout(15.0, connect=10.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            if cfg.yandex_geocoder_api_key:
                return await _yandex_geocode(
                    client, query, cfg.yandex_geocoder_api_key
                )
            return await _nominatim_geocode(
                client, query, cfg.geocoder_user_agent
            )
        except httpx.HTTPStatusError as e:
            logger.warning(
                "Geocoder HTTP error: %s %s",
                e.response.status_code,
                e.request.url,
            )
            raise GeocodeUnavailableError("HTTP error from geocoder") from e
        except httpx.RequestError as e:
            logger.warning("Geocoder request error: %s", e)
            raise GeocodeUnavailableError("Network error to geocoder") from e
