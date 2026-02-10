"""FastAPI application entrypoint."""

import logging

from fastapi import FastAPI

from app.api import auth, buyers, invoices, sellers
from app.core.config import settings
from app.db.session import Base, engine
from app.middleware.logging import LoggingMiddleware

logging.basicConfig(level=logging.INFO)

Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.app_name, openapi_url=f"{settings.api_v1_prefix}/openapi.json")
app.add_middleware(LoggingMiddleware)

app.include_router(auth.router, prefix=settings.api_v1_prefix)
app.include_router(sellers.router, prefix=settings.api_v1_prefix)
app.include_router(buyers.router, prefix=settings.api_v1_prefix)
app.include_router(invoices.router, prefix=settings.api_v1_prefix)


@app.get("/health")
def health() -> dict:
    """Health check."""
    return {"status": "ok"}
