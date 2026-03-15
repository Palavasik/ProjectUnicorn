"""
Окружение Alembic: подключение к БД через DATABASE_URL из .env.
"""

import os
import sys
from pathlib import Path

from alembic import context
from dotenv import load_dotenv

# Корень проекта (родитель каталога alembic)
project_root = Path(__file__).resolve().parent.parent
load_dotenv(project_root / ".env")

# Для импорта моделей из src
sys.path.insert(0, str(project_root / "src"))

from db.models import Base

config = context.config
url = os.getenv("DATABASE_URL")
if not url:
    raise RuntimeError("DATABASE_URL не задан. Задайте в .env или переменных окружения.")
config.set_main_option("sqlalchemy.url", url)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    from alembic import context
    from sqlalchemy import create_engine
    connectable = create_engine(url)
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
