"""Request logging middleware."""

import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("gst_invoice")


class LoggingMiddleware(BaseHTTPMiddleware):
    """Log method, path and response time."""

    async def dispatch(self, request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        duration = (time.perf_counter() - start) * 1000
        logger.info("%s %s -> %s (%.2fms)", request.method, request.url.path, response.status_code, duration)
        return response
