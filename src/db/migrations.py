"""
Запуск миграций Alembic при старте приложения.
Вызывается из main.py, если задан DATABASE_URL.
"""

import logging
import os
import sys
from pathlib import Path

logger = logging.getLogger(__name__)


def run_migrations() -> bool:
    """
    Выполнить alembic upgrade head.
    Возвращает True при успехе, False при отсутствии DATABASE_URL или ошибке.
    """
    if not os.getenv("DATABASE_URL"):
        logger.info("DATABASE_URL не задан — миграции пропущены.")
        return False
    project_root = Path(__file__).resolve().parent.parent.parent
    alembic_ini = project_root / "alembic.ini"
    if not alembic_ini.exists():
        logger.warning("alembic.ini не найден — миграции пропущены.")
        return False
    # Загрузка .env из корня проекта
    try:
        from dotenv import load_dotenv
        load_dotenv(project_root / ".env")
    except Exception:
        pass
    try:
        import alembic.config
        import alembic.command
        alembic_cfg = alembic.config.Config(str(alembic_ini))
        alembic.command.upgrade(alembic_cfg, "head")
        logger.info("Миграции применены (alembic upgrade head).")
        return True
    except Exception as e:
        logger.exception("Ошибка применения миграций: %s", e)
        return False
