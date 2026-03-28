#!/usr/bin/env bash
# Переменные окружения для деплоя бота на Railway.
# Скопируйте этот список в Railway → Variables и подставьте свои значения.
# Не коммитьте реальные ключи в репозиторий.

# --- Обязательные ---
# BOT_TOKEN=                    # Токен от @BotFather
# OPENROUTER_API_KEY=           # Ключ OpenRouter для поиска маршрутов через LLM
# WEBHOOK_URL=                  # Публичный URL сервиса (Railway → Settings → Generate Domain), например https://your-app.up.railway.app

# --- База данных (рекомендуется: ORM, миграции при старте) ---
# Supabase → Settings → Database → Connection string → URI (подставить пароль).
# При задании DATABASE_URL таблицы users/feedback создаются автоматически при первом запуске.
# DATABASE_URL=                 # postgresql://postgres.[ref]:[password]@...pooler.supabase.com:6543/postgres

# --- Supabase REST (только если не задаёте DATABASE_URL) ---
# SUPABASE_URL=                 # https://xxxxx.supabase.co
# SUPABASE_SERVICE_KEY=         # service_role key

# --- Опционально (OpenRouter) ---
# OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
# OPENROUTER_MODEL=openai/gpt-4o-mini
# OPENROUTER_APP_TITLE=Project Unicorn
# OPENROUTER_HTTP_REFERER=
# ROUTE_PROMPT_PATH=config/prompts/route_search.txt
# LOG_LEVEL=INFO
# DEBUG=False

# --- Геокодирование адреса старта (опционально: Яндекс; иначе Nominatim) ---
# GEOCODER_USER_AGENT=MyBot/1.0 (you@example.com)
# YANDEX_GEOCODER_API_KEY=

# --- Логи завершения сценария поиска в отдельный Telegram-чат (опционально) ---
# ANALYTICS_CHAT_ID=            # id группы/канала (часто -100...); бот должен иметь право писать в чат

# PORT задаётся Railway автоматически.
