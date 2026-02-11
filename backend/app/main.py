"""FastAPI application entrypoint."""

import logging

from fastapi import FastAPI
from fastapi.responses import PlainTextResponse

from app.api import auth, buyers, hsn, invoices, sellers
from app.core.config import settings
from app.db.session import Base, SessionLocal, engine
from app.middleware.logging import LoggingMiddleware
from app.services.metrics_service import render_prometheus

logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))

Base.metadata.create_all(bind=engine)


def _seed_hsn_master() -> None:
    from app.models.models import HsnMaster

    defaults = [
        ("1001", "Wheat", 5),
        ("3004", "Medicaments", 12),
        ("4202", "Bags and cases", 18),
        ("8471", "Computers and units", 18),
    ]
    db = SessionLocal()
    try:
        existing = {row.code for row in db.query(HsnMaster).all()}
        for code, description, rate in defaults:
            if code not in existing:
                db.add(HsnMaster(code=code, description=description, default_gst_rate=rate))
        db.commit()
    finally:
        db.close()


_seed_hsn_master()

app = FastAPI(title=settings.app_name, openapi_url=f"{settings.api_v1_prefix}/openapi.json")
app.add_middleware(LoggingMiddleware)

app.include_router(auth.router, prefix=settings.api_v1_prefix)
app.include_router(sellers.router, prefix=settings.api_v1_prefix)
app.include_router(buyers.router, prefix=settings.api_v1_prefix)
app.include_router(hsn.router, prefix=settings.api_v1_prefix)
app.include_router(invoices.router, prefix=settings.api_v1_prefix)


@app.get("/health")
def health() -> dict:
    """Health check."""
    return {"status": "ok"}


@app.get("/metrics", response_class=PlainTextResponse)
def metrics() -> str:
    """Prometheus compatible metrics endpoint."""
    return render_prometheus()
