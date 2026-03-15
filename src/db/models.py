"""
Модели SQLAlchemy для таблиц users и feedback.
Схема совместима с scripts/supabase_schema.sql.
"""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import BigInteger, DateTime, Numeric, SmallInteger, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Базовый класс для моделей."""

    pass


class User(Base):
    """Пользователь Telegram (таблица public.users)."""

    __tablename__ = "users"
    __table_args__ = {"schema": "public"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    telegram_user_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )


class Feedback(Base):
    """Обратная связь после выбора маршрута (таблица public.feedback)."""

    __tablename__ = "feedback"
    __table_args__ = {"schema": "public"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    telegram_user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    route_name: Mapped[str] = mapped_column(Text, nullable=False)
    rating: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    distance_km: Mapped[Optional[Decimal]] = mapped_column(Numeric, nullable=True)
    start_lat: Mapped[Optional[Decimal]] = mapped_column(Numeric, nullable=True)
    start_lon: Mapped[Optional[Decimal]] = mapped_column(Numeric, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
