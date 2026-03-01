# Архитектура приложения

## Общая архитектура MVP

```
┌─────────────┐
│   Telegram  │
│     API     │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Bot Core   │
│  (main.py)  │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Handlers   │
│  (commands, │
│   search,   │
│  messages)  │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Services   │
│ LLM Route   │
│ RouteService│
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Storage   │
│ prompt file │
│ routes.json │
│ user_data   │
└─────────────┘
```

## Поток поиска маршрута

```
/find → [Точка старта: геолокация/координаты] → [Выбор дистанции: 3 кнопки] → вызов OpenAI с промптом из проекта → список маршрутов (название, описание) + под каждым кнопка «Построить маршрут в Яндекс.Картах» → по нажатию: ссылка на Яндекс.Карты с координатами маршрута
```

Состояния диалога: `LOCATION` → `DISTANCE` → `END`. Дистанция — кнопки: короткая (3–5 км), ежедневная (10 км), длинная (18–20 км). Промпт для LLM хранится в `config/prompts/route_search.txt` (или путь из `ROUTE_PROMPT_PATH`).

## Технологический стек MVP

- **Язык**: Python 3.10+
- **Фреймворк**: python-telegram-bot 20.7
- **Поиск маршрутов**: OpenAI (Chat Completions), промпт из файла проекта
- **Карты**: ссылки на Яндекс.Карты (rtext=координаты)
- **Состояние диалога**: in-memory (`context.user_data`)
- **Логирование**: logging (стандартная библиотека)

## 📦 Компоненты системы

### Bot Core (`src/main.py`)
- Инициализация бота
- Настройка роутинга
- Обработка ошибок верхнего уровня

### Handlers (`src/handlers/`)
- **commands.py** — `/start`, `/help`
- **search.py** — `/find`, ConversationHandler (стартовая точка, дистанция → вызов LLM → маршруты с кнопкой «Построить в Яндекс.Картах»), обработчик `route_select` для ссылки на карты, `/cancel`
- **messages.py** — fallback для неизвестных сообщений

### Services (`src/services/`)
- **llm_route_service.py** — вызов OpenAI с промптом из файла (подстановка lat, lon, distance_km), парсинг JSON-ответа с маршрутами (name, description, coordinates)
- **route_service.py** — загрузка маршрутов из JSON (fallback)

### Models (`src/models/`)
- **route.py** — dataclass Route (для JSON), LLMRoute (name, description, coordinates)

### Utils (`src/utils/`)
- **map_links.py** — `build_yandex_route_link(coordinates)` (Яндекс.Карты rtext), `build_route_map_link` (geojson.io)

### Структура `data/routes.json`

Массив объектов маршрутов. Каждый объект:

```json
{
  "id": "msk-gorky-1",
  "city": "Москва",
  "name": "Парк Горького — Нескучный сад",
  "distance_km": 6.0,
  "surface_type": "park",
  "description": "Краткое описание маршрута",
  "features": ["освещение", "мало людей", "без плитки"],
  "map_link": "https://..."
}
```

Типы поверхности: `asphalt`, `park`, `trail`, `embankment`

## Безопасность

- Хранение токенов в переменных окружения
- Валидация входящих данных
- Обработка ошибок без утечки информации
- Rate limiting (при необходимости)

## 📈 Масштабируемость

- Модульная архитектура
- Разделение ответственности
- Возможность горизонтального масштабирования
- Кэширование часто используемых данных
