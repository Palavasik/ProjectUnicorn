"""
Нормализация DATABASE_URL для окружений без IPv6 (например Railway → Supabase).

Прямой хост вида db.<ref>.supabase.co часто резолвится в IPv6; у контейнера нет
маршрута до AAAA → psycopg2: «Network is unreachable». Добавление query-параметра
hostaddr=<IPv4> заставляет libpq подключаться по IPv4, сохраняя host для SSL.
"""

from __future__ import annotations

import logging
import socket
from typing import Optional
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

logger = logging.getLogger(__name__)


def _is_supabase_direct_db_host(hostname: str) -> bool:
    """Хост прямого подключения Supabase (db.<ref>.supabase.co)."""
    return hostname.startswith("db.") and hostname.endswith(".supabase.co")


def normalize_database_url(url: Optional[str]) -> Optional[str]:
    """
    Для прямого Supabase-хоста подставить hostaddr с первым IPv4 из DNS.

    Если в URL уже есть hostaddr или хост не подходит под схему — вернуть как есть.
    """
    if not url:
        return url
    parsed = urlparse(url)
    host = parsed.hostname
    if not host:
        return url

    q = dict(parse_qsl(parsed.query, keep_blank_values=True))
    if q.get("hostaddr"):
        return url

    if not _is_supabase_direct_db_host(host):
        return url

    try:
        infos = socket.getaddrinfo(host, None, socket.AF_INET, socket.SOCK_STREAM)
    except OSError as e:
        logger.warning("Не удалось получить IPv4 для %s: %s", host, e)
        return url

    if not infos:
        logger.warning("Нет IPv4-адресов в DNS для %s", host)
        return url

    ipv4 = infos[0][4][0]
    q["hostaddr"] = ipv4
    new_query = urlencode(q)
    new_parsed = parsed._replace(query=new_query)
    normalized = urlunparse(new_parsed)
    logger.info(
        "DATABASE_URL: для %s добавлен hostaddr=%s (обход отсутствия IPv6 у клиента)",
        host,
        ipv4,
    )
    return normalized
