"""
Сохранение пользователей и обратной связи.
При наличии DATABASE_URL — SQLAlchemy (ORM) и миграции при старте.
Иначе — Supabase REST API (SUPABASE_URL + SUPABASE_SERVICE_KEY).
"""

import logging
from datetime import datetime, timezone
from typing import Any, Optional

from config.settings import Settings

logger = logging.getLogger(__name__)

_supabase_client: Any = None


def _get_supabase_client():
    """Ленивая инициализация клиента Supabase REST."""
    global _supabase_client
    if _supabase_client is not None:
        return _supabase_client
    settings = Settings()
    if not settings.supabase_url or not settings.supabase_service_key:
        return None
    try:
        from supabase import create_client
        _supabase_client = create_client(
            settings.supabase_url,
            settings.supabase_service_key,
        )
        return _supabase_client
    except Exception as e:
        logger.warning("Supabase client init failed: %s", e)
        return None


def _use_orm() -> bool:
    """Использовать ORM (DATABASE_URL) вместо Supabase REST."""
    return bool(Settings().database_url)


def upsert_user(
    telegram_id: int,
    username: Optional[str] = None,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
) -> bool:
    """
    Создать или обновить пользователя по telegram_user_id.
    При DATABASE_URL — через ORM; иначе — через Supabase REST.
    """
    if _use_orm():
        try:
            from db.session import get_session
            from db.repository import upsert_user as repo_upsert_user
            session = get_session()
            if session is None:
                return False
            try:
                return repo_upsert_user(session, telegram_id, username, first_name, last_name)
            finally:
                session.close()
        except Exception as e:
            logger.exception("ORM upsert_user failed: %s", e)
            return False

    client = _get_supabase_client()
    if client is None:
        return False
    now = datetime.now(timezone.utc).isoformat()
    row = {
        "telegram_user_id": telegram_id,
        "username": username,
        "first_name": first_name,
        "last_name": last_name,
        "last_seen_at": now,
    }
    try:
        client.table("users").upsert(row, on_conflict="telegram_user_id").execute()
        return True
    except Exception as e:
        logger.exception("Supabase upsert_user failed: %s", e)
        return False


def insert_feedback(
    telegram_user_id: int,
    route_name: str,
    rating: Optional[int] = None,
    comment: Optional[str] = None,
    distance_km: Optional[float] = None,
    start_lat: Optional[float] = None,
    start_lon: Optional[float] = None,
) -> bool:
    """
    Добавить запись обратной связи после выбора маршрута.
    При DATABASE_URL — через ORM; иначе — через Supabase REST.
    """
    if _use_orm():
        try:
            from db.session import get_session
            from db.repository import insert_feedback as repo_insert_feedback
            session = get_session()
            if session is None:
                return False
            try:
                return repo_insert_feedback(
                    session,
                    telegram_user_id,
                    route_name,
                    rating=rating,
                    comment=comment,
                    distance_km=distance_km,
                    start_lat=start_lat,
                    start_lon=start_lon,
                )
            finally:
                session.close()
        except Exception as e:
            logger.exception("ORM insert_feedback failed: %s", e)
            return False

    client = _get_supabase_client()
    if client is None:
        return False
    row = {
        "telegram_user_id": telegram_user_id,
        "route_name": route_name,
        "rating": rating,
        "comment": comment,
        "distance_km": distance_km,
        "start_lat": start_lat,
        "start_lon": start_lon,
    }
    try:
        client.table("feedback").insert(row).execute()
        return True
    except Exception as e:
        logger.exception("Supabase insert_feedback failed: %s", e)
        return False
