"""
Сервис поиска маршрутов через OpenRouter (OpenAI-совместимый API).
Читает промпт из файла, подставляет параметры, вызывает LLM и парсит JSON-ответ.
"""

import json
import logging
import re
from pathlib import Path
from typing import Optional

from config.settings import Settings

logger = logging.getLogger(__name__)


class LLMRouteServiceError(Exception):
    """Ошибка при вызове LLM или разборе ответа."""

    pass


def _load_prompt(path: str) -> str:
    """Загрузить текст промпта из файла."""
    p = Path(path)
    if not p.exists():
        raise LLMRouteServiceError(f"Файл промпта не найден: {path}")
    return p.read_text(encoding="utf-8")


def _extract_json_from_response(text: str) -> dict:
    """Извлечь JSON из ответа (возможно внутри markdown-блока ```json ... ```)."""
    text = text.strip()
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if match:
        text = match.group(1).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        logger.warning("JSON parse error, trying substring between braces: %s", e)
        start, end = text.find("{"), text.rfind("}")
        if start != -1 and end > start:
            try:
                return json.loads(text[start : end + 1])
            except json.JSONDecodeError:
                pass
        raise


def _validate_route(route: dict, index: int) -> None:
    """Проверить наличие полей и допустимость координат."""
    if not isinstance(route, dict):
        raise LLMRouteServiceError(f"Маршрут {index}: ожидается объект")
    for key in ("name", "description", "coordinates"):
        if key not in route:
            raise LLMRouteServiceError(f"Маршрут {index}: отсутствует поле '{key}'")
    coords = route["coordinates"]
    if not isinstance(coords, list) or len(coords) < 2:
        raise LLMRouteServiceError(f"Маршрут {index}: coordinates должен быть массивом минимум из 2 точек")
    for i, point in enumerate(coords):
        if not isinstance(point, (list, tuple)) or len(point) < 2:
            raise LLMRouteServiceError(f"Маршрут {index}, точка {i}: ожидается [lat, lon]")
        lat, lon = float(point[0]), float(point[1])
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            raise LLMRouteServiceError(f"Маршрут {index}, точка {i}: координаты вне допустимого диапазона")


def get_routes_from_llm(
    lat: float,
    lon: float,
    distance_km: float,
    *,
    prompt_path: Optional[str] = None,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
) -> list[dict]:
    """
    Получить варианты маршрутов от LLM по стартовой точке и дистанции.

    Args:
        lat: Широта старта
        lon: Долгота старта
        distance_km: Желаемая дистанция в км
        prompt_path: Путь к файлу промпта (по умолчанию из настроек)
        api_key: Ключ OpenRouter (по умолчанию из настроек)
        model: Имя модели на OpenRouter (по умолчанию из настроек)

    Returns:
        Список словарей: [{"name": str, "description": str, "coordinates": [[lat, lon], ...]}, ...]

    Raises:
        LLMRouteServiceError: при отсутствии ключа, ошибке API или неверном формате ответа
    """
    settings = Settings()
    path = prompt_path or settings.route_prompt_path
    key = api_key or settings.openrouter_api_key
    model_name = model or settings.openrouter_model

    if not key:
        raise LLMRouteServiceError(
            "Поиск маршрутов через LLM доступен только при настройке OpenRouter. "
            "Укажите OPENROUTER_API_KEY в настройках."
        )

    prompt_text = _load_prompt(path)
    prompt_text = prompt_text.replace("{{lat}}", str(lat))
    prompt_text = prompt_text.replace("{{lon}}", str(lon))
    prompt_text = prompt_text.replace("{{distance_km}}", str(distance_km))

    try:
        from openai import OpenAI
    except ImportError:
        raise LLMRouteServiceError(
            "Пакет openai не установлен. Установите: pip install openai"
        )

    headers = {"X-Title": settings.openrouter_app_title}
    if settings.openrouter_http_referer:
        headers["HTTP-Referer"] = settings.openrouter_http_referer

    client = OpenAI(
        api_key=key,
        base_url=settings.openrouter_base_url,
        default_headers=headers,
    )
    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt_text}],
            temperature=0.3,
        )
    except Exception as e:
        logger.exception("OpenRouter API error: %s", e)
        raise LLMRouteServiceError(
            "Сервис маршрутов временно недоступен. Попробуйте позже."
        ) from e

    content = response.choices[0].message.content
    if not content:
        raise LLMRouteServiceError("Пустой ответ от сервиса маршрутов.")

    try:
        data = _extract_json_from_response(content)
    except json.JSONDecodeError as e:
        logger.warning("Invalid JSON from LLM: %s", e)
        raise LLMRouteServiceError("Не удалось разобрать ответ сервиса маршрутов. Попробуйте ещё раз.") from e

    routes_raw = data.get("routes")
    if not isinstance(routes_raw, list):
        raise LLMRouteServiceError("В ответе отсутствует массив маршрутов (routes).")

    result = []
    for i, r in enumerate(routes_raw):
        _validate_route(r, i)
        result.append({
            "name": str(r["name"]).strip() or f"Маршрут {i + 1}",
            "description": str(r["description"]).strip() or "—",
            "coordinates": [[float(p[0]), float(p[1])] for p in r["coordinates"]],
        })

    logger.info("LLM вернул %d маршрутов для (%.4f, %.4f)", len(result), lat, lon)
    return result
