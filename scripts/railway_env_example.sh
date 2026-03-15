#!/usr/bin/env bash
# Переменные окружения для деплоя бота на Railway.
# Скопируйте этот список в Railway → Variables и подставьте свои значения.
# Не коммитьте реальные ключи в репозиторий.

# --- Обязательные ---
# BOT_TOKEN=                    # Токен от @BotFather
# OPENAI_API_KEY=               # Ключ API OpenAI для поиска маршрутов через LLM
# WEBHOOK_URL=                  # Публичный URL сервиса (Railway → Settings → Generate Domain), например https://your-app.up.railway.app

# --- База данных (рекомендуется: ORM, миграции при старте) ---
# Supabase → Settings → Database → Connection string → URI (подставить пароль).
# При задании DATABASE_URL таблицы users/feedback создаются автоматически при первом запуске.
# DATABASE_URL=                 # postgresql://postgres.[ref]:[password]@...pooler.supabase.com:6543/postgres

# --- Supabase REST (только если не задаёте DATABASE_URL) ---
# SUPABASE_URL=                 # https://xxxxx.supabase.co
# SUPABASE_SERVICE_KEY=         # service_role key

# --- Опционально ---
# OPENAI_MODEL=gpt-4o-mini
# ROUTE_PROMPT_PATH=config/prompts/route_search.txt
# LOG_LEVEL=INFO
# DEBUG=False

# PORT задаётся Railway автоматически.
