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
│ RouteService│
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Storage   │
│ routes.json │
│ user_data   │
└─────────────┘
```

## Поток поиска маршрута

```
/find → [Выбор города] → [Ввод дистанции] → [Выбор поверхности] → Результаты
         (inline)           (текст)              (inline)
```

Состояния диалога: `CITY` → `DISTANCE` → `SURFACE` → `END`

## Технологический стек MVP

- **Язык**: Python 3.10+
- **Фреймворк**: python-telegram-bot 20.7
- **Данные маршрутов**: JSON-файл (`data/routes.json`)
- **Состояние диалога**: in-memory (`context.user_data`)
- **Логирование**: logging (стандартная библиотека)

## 📦 Компоненты системы

### Bot Core (`src/main.py`)
- Инициализация бота
- Настройка роутинга
- Обработка ошибок верхнего уровня

### Handlers (`src/handlers/`)
- **commands.py** — `/start`, `/help`
- **search.py** — `/find`, ConversationHandler (город, дистанция, поверхность), `/cancel`
- **messages.py** — fallback для неизвестных сообщений

### Services (`src/services/`)
- **route_service.py** — загрузка `routes.json`, фильтрация по city/distance/surface_type

### Models (`src/models/`)
- **route.py** — dataclass Route (id, city, name, distance_km, surface_type, description, features, map_link)

### Utils (`src/utils/`)
- Вспомогательные функции
- Утилиты форматирования
- Константы

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
