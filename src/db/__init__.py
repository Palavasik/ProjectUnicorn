"""
Пакет БД: модели, сессии, репозиторий, миграции при старте.
При DATABASE_URL используются SQLAlchemy и миграции Alembic;
иначе — fallback на Supabase REST (supabase_client).
"""

from db.migrations import run_migrations
from db.repository import insert_feedback as repo_insert_feedback
from db.repository import upsert_user as repo_upsert_user
from db.session import get_session, get_session_factory

__all__ = [
    "run_migrations",
    "get_session",
    "get_session_factory",
    "repo_upsert_user",
    "repo_insert_feedback",
]
