"""
Репозиторий: сохранение пользователей и обратной связи через SQLAlchemy.
Используется при наличии DATABASE_URL; иначе — fallback на Supabase REST.
"""

import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from db.models import Feedback, User

logger = logging.getLogger(__name__)


def upsert_user(
    session: Session,
    telegram_id: int,
    username: Optional[str] = None,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
) -> bool:
    """
    Создать или обновить пользователя по telegram_user_id.
    Возвращает True при успехе.
    """
    try:
        now = datetime.now(timezone.utc)
        stmt = insert(User).values(
            telegram_user_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            first_seen_at=now,
            last_seen_at=now,
        ).on_conflict_do_update(
            index_elements=["telegram_user_id"],
            set_={
                "username": username,
                "first_name": first_name,
                "last_name": last_name,
                "last_seen_at": now,
            },
        )
        session.execute(stmt)
        session.commit()
        return True
    except Exception as e:
        logger.exception("ORM upsert_user failed: %s", e)
        session.rollback()
        return False


def insert_feedback(
    session: Session,
    telegram_user_id: int,
    route_name: str,
    rating: Optional[int] = None,
    comment: Optional[str] = None,
    distance_km: Optional[float] = None,
    start_lat: Optional[float] = None,
    start_lon: Optional[float] = None,
) -> bool:
    """Добавить запись обратной связи. Возвращает True при успехе."""
    try:
        row = Feedback(
            telegram_user_id=telegram_user_id,
            route_name=route_name,
            rating=rating,
            comment=comment,
            distance_km=Decimal(str(distance_km)) if distance_km is not None else None,
            start_lat=Decimal(str(start_lat)) if start_lat is not None else None,
            start_lon=Decimal(str(start_lon)) if start_lon is not None else None,
        )
        session.add(row)
        session.commit()
        return True
    except Exception as e:
        logger.exception("ORM insert_feedback failed: %s", e)
        session.rollback()
        return False
