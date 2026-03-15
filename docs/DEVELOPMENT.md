# Руководство по разработке

## 🛠️ Настройка окружения разработки

### 1. Установка зависимостей

```bash
# Создание виртуального окружения
python -m venv venv
source venv/bin/activate  # macOS/Linux
# или
venv\Scripts\activate  # Windows

# Установка зависимостей
pip install -r requirements.txt

# Для разработки (опционально)
pip install -r requirements-dev.txt  # если создадите
```

### 2. Настройка переменных окружения

```bash
cp .env.example .env
# Отредактируйте .env и добавьте ваш BOT_TOKEN
```

### 3. Запуск в режиме разработки

**Локально (polling):**
```bash
python src/main.py
```
При отсутствии `PORT` и `WEBHOOK_URL` бот работает в режиме polling.

При запуске из корня проекта Python автоматически добавляет `src/` в путь поиска модулей.

## 📝 Стандарты кода

### Структура кода

- Используйте type hints для всех функций
- Документируйте функции и классы с помощью docstrings
- Следуйте PEP 8

### Пример кода

```python
from telegram import Update
from telegram.ext import ContextTypes


async def my_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Описание обработчика.
    
    Args:
        update: Объект Update от Telegram
        context: Контекст бота
    """
    # Ваш код здесь
    pass
```

## 🧪 Тестирование

### Запуск тестов

```bash
pytest
```

### Запуск с покрытием

```bash
pytest --cov=src --cov-report=html
```

## 📦 Структура модулей

### Добавление новой команды

1. Создайте обработчик в `src/handlers/commands.py`:

```python
async def my_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Ответ")
```

2. Зарегистрируйте в `src/bot/bot.py`:

```python
self.application.add_handler(CommandHandler("mycommand", my_command_handler))
```

### Добавление обработчика сообщений

1. Создайте обработчик в `src/handlers/messages.py` или создайте новый файл
2. Зарегистрируйте в `src/bot/bot.py`

### Добавление сервиса

1. Создайте файл в `src/services/`
2. Реализуйте бизнес-логику
3. Импортируйте и используйте в обработчиках

## 🔍 Отладка

### Логирование

Используйте стандартный модуль logging:

```python
import logging

logger = logging.getLogger(__name__)
logger.info("Информационное сообщение")
logger.error("Ошибка", exc_info=True)
```

### Тестирование локально

Для тестирования без реального бота используйте моки:

```python
from unittest.mock import AsyncMock, MagicMock

update = MagicMock()
update.message.reply_text = AsyncMock()
```

## Деплой

### Railway (webhook)

1. Подключите репозиторий к [Railway](https://railway.app).
2. В Variables задайте `BOT_TOKEN`, `OPENAI_API_KEY` (для поиска маршрутов через LLM), `WEBHOOK_URL` (публичный URL сервиса после генерации домена), а также `SUPABASE_URL` и `SUPABASE_SERVICE_KEY` для хранения пользователей и обратной связи.
3. Деплой по push; бот запускается через `Procfile` в режиме webhook.
4. Подробнее: раздел «Деплой на Railway» в [README](../README.md). Пошаговая развёртка Supabase и настройка переменных Railway: [DEPLOY_SUPABASE_RAILWAY.md](DEPLOY_SUPABASE_RAILWAY.md).
