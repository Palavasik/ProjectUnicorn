"""
Тесты для обработчиков.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from handlers.commands import start_handler, help_handler


@pytest.mark.asyncio
async def test_start_handler():
    """Тест обработчика команды /start."""
    # Создание моков
    update = MagicMock()
    update.effective_user.first_name = "Test"
    update.message.reply_text = AsyncMock()
    context = MagicMock()
    
    # Вызов обработчика
    await start_handler(update, context)
    
    # Проверка
    update.message.reply_text.assert_called_once()


@pytest.mark.asyncio
async def test_help_handler():
    """Тест обработчика команды /help."""
    # Создание моков
    update = MagicMock()
    update.message.reply_text = AsyncMock()
    context = MagicMock()
    
    # Вызов обработчика
    await help_handler(update, context)
    
    # Проверка
    update.message.reply_text.assert_called_once()
