# Project Unicorn — Telegram Bot

## Описание

**Project Unicorn** — Telegram-бот для бегунов-любителей. Помогает быстро найти маршруты для бега от вашей точки: по геолокации и выбранной дистанции LLM предлагает варианты маршрутов; по нажатию кнопки открывается построение маршрута в Яндекс.Картах.

*«Найти, где побегать в незнакомом городе — быстро и по своим правилам»*

## Быстрый старт

### Требования

- Python 3.10+
- Telegram Bot Token ([@BotFather](https://t.me/BotFather))

### Установка

```bash
git clone <repository-url>
cd ProjectUnicorn

python -m venv venv
source venv/bin/activate   # macOS/Linux
# venv\Scripts\activate    # Windows

pip install -r requirements.txt

cp .env.example .env
# Добавьте BOT_TOKEN и OPENAI_API_KEY в .env
# Промпт для LLM: config/prompts/route_search.txt (или ROUTE_PROMPT_PATH)
```

### Запуск (локально)

```bash
python src/main.py
```

Локально используется **polling**. На Railway — **webhook** (см. ниже).

### Деплой на Railway

1. Создайте проект на [Railway](https://railway.app) и подключите репозиторий.
2. В **Variables** задайте:
   - `BOT_TOKEN` — токен от [@BotFather](https://t.me/BotFather)
   - `OPENAI_API_KEY` — ключ OpenAI для поиска маршрутов через LLM
   - `WEBHOOK_URL` — публичный URL сервиса (Railway → Settings → Generate Domain; например `https://your-app.up.railway.app`)
3. `PORT` и домен Railway задаются автоматически.
4. Деплой по push в ветку; бот запустится в режиме webhook.

Файлы для Railway: `Procfile`, `runtime.txt`, `railway.json`.

### Команды бота

| Команда | Описание |
|---------|----------|
| `/start` | Приветствие и описание возможностей |
| `/find` | Найти маршрут (точка старта → дистанция → маршруты от LLM → ссылка на Яндекс.Карты) |
| `/cancel` | Отменить текущий поиск |
| `/help` | Список команд |

## Структура проекта

```
ProjectUnicorn/
├── data/
│   └── routes.json        # Маршруты для поиска
├── docs/
│   ├── product/          # Карточка продукта, ЦА, боли
│   ├── bot/               # MVP_SPEC, спецификация бота
│   ├── architecture/      # Архитектура
│   └── api/               # API документация
├── src/
│   ├── bot/               # Инициализация бота
│   ├── handlers/          # commands, search, messages
│   ├── services/          # llm_route_service, route_service
│   ├── models/            # Route
│   └── main.py            # Точка входа
├── tests/
├── .env.example
├── requirements.txt
└── README.md
```

## Документация

- [Карточка продукта](docs/product/PRODUCT_CARD.md)
- [Спецификация MVP бота](docs/bot/MVP_SPEC.md)
- [Архитектура](docs/architecture/README.md)
- [API документация](docs/api/README.md)
- [Настройка GitHub и релизов](docs/GITHUB_SETUP.md)
- [Руководство по разработке](docs/DEVELOPMENT.md)

## 🔗 Подключение к GitHub

Для подключения проекта к GitHub и настройки релизов см. [инструкцию](docs/GITHUB_SETUP.md).

Быстрая настройка:
```bash
# Используйте скрипт для автоматической настройки
./scripts/setup-github.sh YOUR_USERNAME ProjectUnicorn

# Или выполните вручную:
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/ProjectUnicorn.git
git branch -M main
git push -u origin main
```

## 🤝 Вклад в проект

[Описание процесса контрибуции]

## 📄 Лицензия

[Указать лицензию]
