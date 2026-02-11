# GST Invoice Generator (Industry Grade, India)

Production-ready GST invoice system for Indian shopkeepers with FastAPI + React + SQLite, designed for deployment and MuleRun packaging.

## Highlights
- JWT auth preserved (`/auth/register`, `/auth/login`)
- Strict GSTIN validation (regex + PAN segment + state-code match)
- HSN master + item-level HSN validation (4–8 digits)
- Hardened GST rules engine:
  - Intra-state → CGST/SGST
  - Inter-state → IGST
  - Export → zero-rated
  - Reverse charge indicator
  - Composition dealer (no tax charged)
- Deterministic rounding (line-level round then invoice recompute)
- Invoice locking (`DRAFT` → `FINAL`, immutable after finalization)
- Idempotent create (`Idempotency-Key` header)
- Rate limiting:
  - login: 10/min
  - invoice create: 30/min
- Structured JSON logs (`user_id`, `invoice_id`, `action`, `latency_ms`)
- Export outputs:
  - PDF with proper GST layout + QR (invoice id)
  - GST-filing JSON schema
  - A4 print HTML
- MuleRun compatibility:
  - `/health`
  - `/metrics`
  - env-driven config
  - stateless service behavior

## Tech Stack
- **Backend**: FastAPI, SQLAlchemy, Alembic, SQLite, reportlab
- **Frontend**: React, Tailwind, Vite
- **Auth**: JWT

## Repo Structure
```text
backend/
  app/
    api/
    core/
    db/
    middleware/
    models/
    schemas/
    services/
    utils/
  alembic/
  tests/
frontend/
  src/
```

## Environment Variables (required)
Create `backend/.env`:
```env
JWT_SECRET_KEY=replace-with-strong-secret
DATABASE_URL=sqlite:///./gst_invoice.db
ACCESS_TOKEN_EXPIRE_MINUTES=60
JWT_ALGORITHM=HS256
LOG_LEVEL=INFO
APP_NAME=GST Invoice Generator
API_V1_PREFIX=/api/v1
```

## Backend Run
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

## Frontend Run
```bash
cd frontend
npm install
npm run dev
```

## Important Endpoints
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `GET /health`
- `GET /metrics`
- `GET /api/v1/hsn`
- `POST /api/v1/invoices` (supports `Idempotency-Key`)
- `PUT /api/v1/invoices/{invoice_id}` (blocked after `FINAL`)
- `POST /api/v1/invoices/{invoice_id}/finalize`
- `GET /api/v1/invoices/{invoice_id}/pdf`
- `GET /api/v1/invoices/{invoice_id}/json`
- `GET /api/v1/invoices/{invoice_id}/print`

## Testing
```bash
cd backend
PYTHONPATH=. pytest -q
```

## Coverage
To verify service coverage target:
```bash
cd backend
PYTHONPATH=. pytest --cov=app.services --cov-report=term-missing
```


## UI/UX Enhancements (Shopkeeper-Optimized)
- Reusable invoice builder components (`components/invoice/*`)
- Form state hooks (`hooks/useInvoiceForm`, `hooks/useInvoiceValidation`, `hooks/useDebouncedValue`)
- Offline-safe autosave draft in localStorage
- Debounced live tax calculation preview + GST split panel
- Instant add/remove line items with keyboard shortcut (`Ctrl/Cmd + N`)
- Inline validation highlights for line item errors
- High contrast mode toggle for accessibility
- Screen-reader labels on key form fields

## PDF Template Enhancements
- Professional layout with optional company logo
- QR code for invoice ID
- Terms & conditions section
- Signature block with configurable signatory
- Print-optimized A4 export
