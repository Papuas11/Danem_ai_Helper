# danem-sales-copilot

Greenfield MVP sales workflow tool для DANEM.

## Стек
- Backend: Python 3.11, FastAPI, SQLAlchemy, SQLite, Pydantic, Uvicorn
- Frontend: Next.js, React, TypeScript

## Структура
- `backend/` — API, модели, сервисы анализа/пересчёта, seed
- `frontend/` — UI с тремя вкладками: AI помощник, база приборов, история сделок

## Функции MVP
- Разбор свободного текста в структурированные поля сделки.
- Расчёт цены/себестоимости/прибыли/маржи.
- Rule-based вероятность сделки.
- Полнота заявки, checklist недостающих данных, 3 следующих шага.
- Черновик ответа клиенту.
- Warning flags.
- Ручные правки и пересчёт.
- CRUD приборов/aliases/услуг.
- История сделок, события и снапшоты, похожие сделки.
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
- Deals: `GET/POST /api/deals`, `GET/PUT /api/deals/{id}`
- Analysis: `POST /api/deals/analyze`, `POST /api/deals/{id}/recalculate`, `POST /api/deals/{id}/finalize`
- History: `GET /api/deals/{id}/events`, `GET /api/deals/{id}/snapshots`, `GET /api/deals/{id}/similar`

## Seed data
При старте backend автоматически добавляются:
- 3 прибора: Manometer, Pyrometer, Thermometer
- aliases для Manometer (включая русские формы)
- минимум по 1 услуге на прибор
- 3 примерные сделки
