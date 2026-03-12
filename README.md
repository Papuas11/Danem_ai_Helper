# danem-sales-copilot

Greenfield local MVP for DANEM managers. Built for Python 3.11 + FastAPI backend and Next.js TypeScript frontend.

## Project Structure

- `backend/` FastAPI, SQLAlchemy, SQLite, seed data, analysis services.
- `frontend/` Next.js app with 3 tabs: Manager AI, Instruments Database, Deal History.

## Backend Setup (Python 3.11)

```bash
cd backend
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

API base: `http://localhost:8000`

### Implemented endpoints

- Instruments: GET/POST `/api/instruments`, GET/PUT/DELETE `/api/instruments/{id}`
- Aliases: POST `/api/instruments/{id}/aliases`, DELETE `/api/aliases/{alias_id}`
- Services: POST `/api/instruments/{id}/services`, PUT/DELETE `/api/services/{service_id}`
- Deals: GET/POST `/api/deals`, GET/PUT `/api/deals/{id}`
- Analysis: POST `/api/deals/analyze`, POST `/api/deals/{id}/recalculate`, POST `/api/deals/{id}/finalize`
- History: GET `/api/deals/{id}/events`, `/api/deals/{id}/snapshots`, `/api/deals/{id}/similar`

## Frontend Setup

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

Frontend URL: `http://localhost:3000`

## MVP Features

- Free-text parsing into structured deal data (instrument/service/quantity/onsite/urgency/confidence).
- Economics calculation (price/cost/profit/margin, onsite logic).
- Completeness score + missing fields.
- Rule-based deal probability (5–95).
- Exactly 3 next manager actions.
- Draft reply generation.
- Warning flags.
- Manual edits and recalculation with event + snapshot history.
- Instruments DB with instrument/alias/service separation.
- Deal history and similar deal guidance.
- Internet enrichment mode scaffold (`OFF` default, no auto DB changes).

## Seed Data

On first backend startup, database is seeded with:

- Instruments: Manometer, Pyrometer, Thermometer
- Manometer aliases including Russian forms + pressure gauge / gauge
- One service per instrument
- 3 sample deals

## Notes

- Designed for stable local startup and empty-safe UI states.
- SQLite stores list-like fields as JSON strings for practical portability.
