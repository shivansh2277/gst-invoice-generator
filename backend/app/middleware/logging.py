"""Request logging middleware with JSON logs and lightweight metrics."""

import json
import logging
import re
import time

from starlette.middleware.base import BaseHTTPMiddleware

from app.core.security import decode_access_token
from app.services.metrics_service import inc

logger = logging.getLogger("gst_invoice")
invoice_path_re = re.compile(r"/invoices/(\d+)")


class LoggingMiddleware(BaseHTTPMiddleware):
    """Log method, path, user and response time as JSON."""

    async def dispatch(self, request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        duration = (time.perf_counter() - start) * 1000
        auth_header = request.headers.get("Authorization", "")
        token = auth_header.split(" ", 1)[1] if auth_header.startswith("Bearer ") else ""
        user_id = decode_access_token(token) if token else None
        matched = invoice_path_re.search(request.url.path)
        invoice_id = int(matched.group(1)) if matched else None
        action = f"{request.method} {request.url.path}"
        payload = {
            "user_id": user_id,
            "invoice_id": invoice_id,
            "action": action,
            "latency_ms": round(duration, 2),
            "status_code": response.status_code,
        }
        logger.info(json.dumps(payload))
        inc("http_requests_total")
        return response
