"""
Сессия БД: движок и фабрика сессий SQLAlchemy.
Использует DATABASE_URL из настроек.
"""

import logging
from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from config.settings import Settings
from db.models import Base

logger = logging.getLogger(__name__)

_engine = None
_SessionLocal: Optional[sessionmaker] = None


def get_engine():
    """Создать или вернуть движок (ленивая инициализация)."""
    global _engine
    if _engine is not None:
        return _engine
    settings = Settings()
    if not settings.database_url:
        return None
    try:
        _engine = create_engine(
            settings.database_url,
            pool_pre_ping=True,
            echo=settings.debug,
        )
        return _engine
    except Exception as e:
        logger.warning("DB engine init failed: %s", e)
        return None


def get_session_factory():
    """Фабрика сессий. Возвращает None, если DATABASE_URL не задан."""
    global _SessionLocal
    if _SessionLocal is not None:
        return _SessionLocal
    engine = get_engine()
    if engine is None:
        return None
    _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return _SessionLocal


def get_session() -> Optional[Session]:
    """Новая сессия для использования в with get_session() as session."""
    factory = get_session_factory()
    if factory is None:
        return None
    return factory()
