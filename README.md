# danem-sales-copilot

Greenfield MVP sales workflow tool для DANEM.

## Стек
- Backend: Python 3.11, FastAPI, SQLAlchemy, SQLite, Pydantic, Uvicorn
- Frontend: Next.js, React, TypeScript
- AI backend layer: OpenAI Responses API (optional, fallback-safe)

## Структура
- `backend/` — API, модели, сервисы анализа/пересчёта, seed
- `frontend/` — UI с тремя вкладками: AI помощник, база приборов, история сделок

## Гибридная архитектура (AI + deterministic backend)
- Детеминированная backend-логика и БД остаются источником истины для:
  - цены/себестоимости/прибыли/маржи
  - onsite-надбавок
  - unit-множителей
  - правил обязательных данных и валидации по базе
- AI используется как decision-support слой для:
  - парсинга messy free-text заявок
  - анализа недостающих данных и рекомендаций
  - генерации 3 next steps
  - генерации черновика ответа клиенту
  - explainability вероятности сделки
  - summary похожих сделок
  - review оценки и риск-заметок
  - анализа финального отклонения
  - ассистента по alias/category/service suggestions в табе базы приборов
- При ошибке AI или отсутствии ключа всегда используется безопасный rule-based fallback без падения API.

## Конфигурация окружения
Создайте `.env` в `backend/` (или экспортируйте переменные):

```bash
OPENAI_ENABLED=false
AI_PROVIDER=openai
AI_MODE=hybrid
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4.1-mini
OPENAI_TIMEOUT_SECONDS=10
```

### Переменные
- `OPENAI_ENABLED` — `true/false`, включает AI-вызовы на backend.
- `AI_PROVIDER` — сейчас поддерживается `openai`.
- `AI_MODE` — режим гибридного поведения (`hybrid` по умолчанию).
- `OPENAI_API_KEY` — ключ OpenAI API (только из env, не хардкодится).
- `OPENAI_MODEL` — модель для Responses API.
- `OPENAI_TIMEOUT_SECONDS` — timeout AI-запросов.

> Если `OPENAI_API_KEY` отсутствует/некорректен, либо API недоступен, backend автоматически продолжает работу по текущей rule-based логике.

## Функции MVP
- Разбор свободного текста в структурированные поля сделки.
- Расчёт цены/себестоимости/прибыли/маржи (deterministic backend).
- Rule-based вероятность сделки + AI explanation.
- Полнота заявки, checklist недостающих данных, 3 следующих шага.
- Черновик ответа клиенту.
- Warning flags (deterministic + AI risk notes).
- Ручные правки и пересчёт.
- CRUD приборов/aliases/услуг.
- История сделок, события и снапшоты, похожие сделки.
- AI-ассист endpoint для suggestions по прибору (только suggestions, без автосохранения).
- Scaffold internet enrichment mode: OFF/WHITELIST/FULL (по умолчанию OFF).

## Запуск backend
```bash
cd backend
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## Запуск frontend
```bash
cd frontend
npm install
npm run dev
```

Frontend: http://localhost:3000  
Backend: http://localhost:8000  
Health: http://localhost:8000/health

## Основные API
- Instruments: `GET/POST /api/instruments`, `GET/PUT/DELETE /api/instruments/{id}`
- Aliases: `POST /api/instruments/{id}/aliases`, `DELETE /api/aliases/{alias_id}`
- Services: `POST /api/instruments/{id}/services`, `PUT/DELETE /api/services/{service_id}`
- Instrument AI assist: `POST /api/instruments/assist`
- Deals: `GET/POST /api/deals`, `GET/PUT /api/deals/{id}`
- Analysis: `POST /api/deals/analyze`, `POST /api/deals/{id}/recalculate`, `POST /api/deals/{id}/finalize`
- History: `GET /api/deals/{id}/events`, `GET /api/deals/{id}/snapshots`, `GET /api/deals/{id}/similar`

## Seed data
При старте backend автоматически добавляются:
- 3 прибора: Manometer, Pyrometer, Thermometer
- aliases для Manometer (включая русские формы)
- минимум по 1 услуге на прибор
- 3 примерные сделки
