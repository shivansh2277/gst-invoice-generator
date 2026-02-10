# GST Invoice Generator (India)

Production-oriented GST Invoice Generator for Indian shopkeepers.

## Stack
- **Backend**: FastAPI + SQLAlchemy + Alembic + SQLite
- **Frontend**: React + Tailwind + Vite
- **PDF**: reportlab
- **Auth**: JWT

## Features
- JWT login/register
- Create and update draft invoices (B2B/B2C)
- Auto invoice number increment (`INV-YYYY-00001`)
- GSTIN format + state code validation
- Intra/inter state detection and CGST/SGST/IGST split
- Reverse charge support
- GST-compliant rounding (half-up, 2 decimals)
- Grand total in words
- Finalize and lock invoice
- Export invoice as JSON, PDF and print-friendly HTML
- OpenAPI docs available at `/docs`
- Logging middleware with latency metrics
- Unit tests for deterministic tax engine

## Repository structure

```text
backend/
  app/
    api/            # Route handlers
    core/           # Config/security
    db/             # SQLAlchemy engine/session
    middleware/     # Logging middleware
    models/         # Normalized database models
    schemas/        # Pydantic schemas
    services/       # Tax and PDF logic
    utils/          # GST validation and number-to-words
  alembic/          # Migration environment and revisions
  tests/            # Unit tests
frontend/
  src/
    components/
    pages/
    services/
```

## Data model
Normalized schema:
- `users`
- `sellers`
- `buyers`
- `invoices`
- `invoice_items`
- `tax_summary`

## Backend setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

Backend URL: `http://localhost:8000`
- Swagger docs: `http://localhost:8000/docs`
- OpenAPI JSON: `http://localhost:8000/api/v1/openapi.json`

## Frontend setup

```bash
cd frontend
npm install
npm run dev
```

Frontend URL: `http://localhost:5173`

## Main API endpoints
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `POST /api/v1/sellers`
- `GET /api/v1/sellers`
- `POST /api/v1/buyers`
- `GET /api/v1/buyers`
- `POST /api/v1/invoices`
- `PUT /api/v1/invoices/{invoice_id}`
- `POST /api/v1/invoices/{invoice_id}/finalize`
- `GET /api/v1/invoices/{invoice_id}/json`
- `GET /api/v1/invoices/{invoice_id}/pdf`
- `GET /api/v1/invoices/{invoice_id}/print`

## Testing

```bash
cd backend
PYTHONPATH=. pytest -q
```
