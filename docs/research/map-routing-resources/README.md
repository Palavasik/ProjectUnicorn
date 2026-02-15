# Открытые ресурсы с картами и маршрутизацией

Исследование открытых API и сервисов для поиска маршрутов по критериям: **локация**, **длина**, **тип покрытия**.

---

## 1. OpenRouteService

**Сайт:** [openrouteservice.org](https://openrouteservice.org)  
**API:** [api.openrouteservice.org](https://api.openrouteservice.org)  
**Лицензия:** Open Source (Apache 2.0), бесплатный тариф с лимитами

### Возможности

| Критерий | Поддержка |
|----------|-----------|
| **Локация** | ✅ Координаты, геокодинг, изохроны |
| **Длина** | ✅ Расстояние в ответе, ограничение до 6000 км |
| **Тип покрытия** | ✅ Extra Info `surface` — 18 типов (asphalt, gravel, dirt, grass и др.) |

### Типы поверхности (Extra Info)

- Paved, Unpaved, Asphalt, Concrete
- Metal, Wood, Compacted Gravel, Gravel
- Dirt, Ground, Ice, Paving Stones
- Sand, Grass, Grass Paver, Unknown

### Профили маршрутизации

- Пешеходы (foot-walking)
- Велосипед (cycling-regular, cycling-road, cycling-mountain)
- Хайкинг (hiking)
- Инвалидные коляски (wheelchair) — с параметром `surface_type` для минимального качества покрытия

### Лимиты бесплатного тарифа

- Directions: до 6000 км, до 50 waypoints
- Isochrones: до 5 локаций, до 10 интервалов, радиус до 120 км
- Matrix: до 3500 локаций (50×50)
- Квоты сбрасываются каждые 24 часа

### Использование

```http
POST /v2/directions/driving-car
{
  "coordinates": [[lon1, lat1], [lon2, lat2]],
  "extra_info": ["surface"]
}
```

Ответ: `$.routes[*].extras.surface.values` — сегменты с типом покрытия.

---

## 2. GraphHopper

**Сайт:** [graphhopper.com](https://www.graphhopper.com)  
**Документация:** [docs.graphhopper.com](https://docs.graphhopper.com)  
**Лицензия:** Apache 2.0 (self-hosted), облачный API с бесплатным тарифом

### Возможности

| Критерий | Поддержка |
|----------|-----------|
| **Локация** | ✅ Координаты, геокодинг |
| **Длина** | ✅ Расстояние в ответе |
| **Тип покрытия** | ✅ Custom Model — атрибут `surface` |

### Road attributes (Custom Model)

- **surface:** PAVED, DIRT, SAND, GRAVEL, …
- **smoothness:** EXCELLENT, GOOD, INTERMEDIATE, …
- **road_class:** MOTORWAY, TRUNK, PRIMARY, TRACK, CYCLEWAY, FOOTWAY, …
- **track_type:** GRADE1–GRADE5
- **hike_rating, mtb_rating:** 0–6 (SAC scale)

### Custom Model

Позволяет задавать правила маршрутизации без кода, например:

- «Снизить скорость на гравийных третичных дорогах»
- «Предпочитать асфальт»
- «Избегать грунтовых дорог»

### Использование

```http
POST /route
{
  "points": [[lon1, lat1], [lon2, lat2]],
  "profile": "bike",
  "custom_model": {
    "areas": {},
    "speed": [{"if": "surface == GRAVEL", "multiply_by": "0.7"}]
  },
  "details": ["surface"]
}
```

---

## 3. OSRM (Open Source Routing Machine)

**Сайт:** [project-osrm.org](https://project-osrm.org)  
**GitHub:** [Project-OSRM/osrm-backend](https://github.com/Project-OSRM/osrm-backend)  
**Лицензия:** BSD 2-Clause, полностью open source

### Возможности

| Критерий | Поддержка |
|----------|-----------|
| **Локация** | ✅ Координаты |
| **Длина** | ✅ Расстояние в ответе |
| **Тип покрытия** | ⚠️ Ограниченно — в данных OSM есть, но не в стандартных параметрах API |

### Профили

- car, bike, foot

### Особенности

- Быстрый, оптимизированный роутер
- Self-hosted — полный контроль
- Нет встроенной фильтрации по surface в публичном API
- Подходит для базовой маршрутизации без учёта покрытия

---

## 4. Valhalla

**Сайт:** [valhalla.github.io](https://valhalla.github.io/valhalla)  
**GitHub:** [valhalla/valhalla](https://github.com/valhalla/valhalla)  
**Лицензия:** MIT, open source

### Возможности

| Критерий | Поддержка |
|----------|-----------|
| **Локация** | ✅ Координаты |
| **Длина** | ✅ Расстояние в ответе |
| **Тип покрытия** | ✅ Surface как атрибут ребра в Trip Path |

### Особенности

- Surface хранится как атрибут ребра
- Плагинная архитектура — можно учитывать surface в costing
- Поддержка OSM тегов для routing
- Self-hosted

---

## 5. Overpass API (OpenStreetMap)

**Сайт:** [wiki.openstreetmap.org/wiki/Overpass_API](https://wiki.openstreetmap.org/wiki/Overpass_API)  
**Публичные инстансы:** overpass-api.de, overpass.kumi.systems  
**Лицензия:** ODbL (данные OSM)

### Возможности

| Критерий | Поддержка |
|----------|-----------|
| **Локация** | ✅ Bounding box, полигон, радиус |
| **Длина** | ⚠️ Можно вычислить по геометрии ways |
| **Тип покрытия** | ✅ Тег `surface=*` |

### Использование

Overpass не строит маршруты, но позволяет **выбрать дороги/тропы** по критериям:

```overpass
[out:json][timeout:25];
(
  way["highway"~"path|footway|cycleway"]["surface"="asphalt"](around:5000,55.75,37.62);
);
out body;
>;
out skel qt;
```

### Теги surface в OSM

- **Paved:** asphalt, concrete, paving_stones, sett, cobblestone, bricks
- **Unpaved:** gravel, fine_gravel, compacted, dirt, ground, grass, sand, mud
- **Special:** tartan, clay, artificial_turf (беговые дорожки)

[Полный список](https://wiki.openstreetmap.org/wiki/Key:surface)

---

## 6. Российские сервисы

| Сервис | Маршруты | Тип покрытия | Бесплатно |
|--------|----------|--------------|-----------|
| **Яндекс Router API** | Пешеходы, велосипед, авто | ❌ Нет | Тестовый период |
| **2GIS Directions API** | Пешеходы, велосипед, авто, самокат | ❌ Нет | Демо-ключ |
| **OpenTripMap** | POI, тайлы | ❌ Нет | Экспериментально |

Полностью бесплатных API для маршрутов с фильтром по покрытию в России нет. OSM-based сервисы (OpenRouteService, GraphHopper) работают с данными OSM по России, но покрытие может быть менее детализировано, чем в Европе.

---

## Сравнение по критериям

| Ресурс | Локация | Длина | Тип покрытия | Бесплатно | Self-hosted |
|--------|---------|-------|--------------|-----------|-------------|
| **OpenRouteService** | ✅ | ✅ | ✅ Extra Info | ✅ Лимиты | ✅ |
| **GraphHopper** | ✅ | ✅ | ✅ Custom Model | ✅ Лимиты | ✅ |
| **OSRM** | ✅ | ✅ | ⚠️ | ✅ | ✅ |
| **Valhalla** | ✅ | ✅ | ✅ В costing | ✅ | ✅ |
| **Overpass API** | ✅ | ⚠️ | ✅ | ✅ | ✅ |

---

## Рекомендации для ProjectUnicorn

Для бота поиска беговых маршрутов по городу, дистанции и типу покрытия:

1. **OpenRouteService** — оптимальный выбор для MVP:
   - Бесплатный API с лимитами
   - Профили foot-walking, hiking
   - Extra Info `surface` в ответе
   - Не требует self-hosting

2. **GraphHopper** — альтернатива с Custom Model:
   - Гибкая настройка предпочтений по surface
   - Параметр `details: ["surface"]` в ответе

3. **Overpass API** — для кастомной логики:
   - Поиск дорог/троп по surface в заданной области
   - Построение маршрута — отдельно (OSRM/ORS)

4. **Маппинг surface** на текущие типы в `route_service.py`:
   - `asphalt` → asphalt
   - `grass`, `ground` → park
   - `gravel`, `dirt`, `compacted` → trail
   - `paving_stones`, набережные (по тегу) → embankment

---

## Ссылки

- [OpenRouteService API Reference](https://giscience.github.io/openrouteservice/api-reference/)
- [GraphHopper Custom Model](https://docs.graphhopper.com/openapi/custom-model/)
- [OSM Key:surface](https://wiki.openstreetmap.org/wiki/Key:surface)
- [Overpass API](https://wiki.openstreetmap.org/wiki/Overpass_API)
- [Valhalla API](https://valhalla.github.io/valhalla/api/)
