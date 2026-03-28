"""Тесты geocode_service (моки httpx, без реальных запросов)."""

import unittest
from unittest.mock import AsyncMock, MagicMock, patch

import httpx

from services.geocode_service import (
    GeocodeUnavailableError,
    geocode_to_lat_lon,
)


def _mock_async_client(mock_get: AsyncMock) -> MagicMock:
    mock_client = MagicMock()
    mock_client.get = mock_get
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    return mock_client


class TestGeocodeService(unittest.IsolatedAsyncioTestCase):
    async def test_nominatim_success(self) -> None:
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = [
            {
                "lat": "55.7558",
                "lon": "37.6173",
                "display_name": "Moscow, Red Square",
            }
        ]
        mock_get = AsyncMock(return_value=mock_resp)
        mock_client = _mock_async_client(mock_get)

        settings = MagicMock()
        settings.yandex_geocoder_api_key = None
        settings.geocoder_user_agent = "TestBot/1.0"

        with patch("services.geocode_service.httpx.AsyncClient", return_value=mock_client):
            r = await geocode_to_lat_lon("Moscow Red Square", settings)

        self.assertIsNotNone(r)
        assert r is not None
        self.assertAlmostEqual(r.lat, 55.7558)
        self.assertAlmostEqual(r.lon, 37.6173)
        self.assertEqual(r.display_name, "Moscow, Red Square")
        mock_get.assert_awaited_once()

    async def test_nominatim_empty_returns_none(self) -> None:
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = []
        mock_client = _mock_async_client(AsyncMock(return_value=mock_resp))

        settings = MagicMock()
        settings.yandex_geocoder_api_key = None
        settings.geocoder_user_agent = "TestBot/1.0"

        with patch("services.geocode_service.httpx.AsyncClient", return_value=mock_client):
            r = await geocode_to_lat_lon("nowhere xyz", settings)

        self.assertIsNone(r)

    async def test_yandex_success(self) -> None:
        yandex_json = {
            "response": {
                "GeoObjectCollection": {
                    "featureMember": [
                        {
                            "GeoObject": {
                                "name": "улица Ленина, 1",
                                "description": "Москва",
                                "Point": {"pos": "37.62 55.76"},
                            }
                        }
                    ]
                }
            }
        }
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = yandex_json
        mock_client = _mock_async_client(AsyncMock(return_value=mock_resp))

        settings = MagicMock()
        settings.yandex_geocoder_api_key = "test-yandex-key"
        settings.geocoder_user_agent = "ignored"

        with patch("services.geocode_service.httpx.AsyncClient", return_value=mock_client):
            r = await geocode_to_lat_lon("Ленина 1 Москва", settings)

        self.assertIsNotNone(r)
        assert r is not None
        self.assertAlmostEqual(r.lat, 55.76)
        self.assertAlmostEqual(r.lon, 37.62)
        self.assertIn("Ленина", r.display_name)

    async def test_request_error_raises_unavailable(self) -> None:
        mock_client = _mock_async_client(
            AsyncMock(side_effect=httpx.ConnectError("refused", request=MagicMock()))
        )
        settings = MagicMock()
        settings.yandex_geocoder_api_key = None
        settings.geocoder_user_agent = "TestBot/1.0"

        with patch("services.geocode_service.httpx.AsyncClient", return_value=mock_client):
            with self.assertRaises(GeocodeUnavailableError):
                await geocode_to_lat_lon("x", settings)


if __name__ == "__main__":
    unittest.main()
