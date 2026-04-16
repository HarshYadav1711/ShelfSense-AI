"""
Lightweight request timing and access-style logging (console only).

Logs method, path (no query string), response status, and elapsed time.
Intentionally omits headers, bodies, and query strings to avoid leaking secrets.
"""

from __future__ import annotations

import logging
import time
from typing import Callable

from django.http import HttpRequest, HttpResponse

logger = logging.getLogger("shelfsense.request")


class RequestTimingMiddleware:
    """Measure full downstream processing time (inner middleware + view)."""

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        start = time.perf_counter()
        response = self.get_response(request)
        elapsed_ms = (time.perf_counter() - start) * 1000.0

        # Path only — excludes query strings (tokens, search terms, etc.).
        path = request.path
        method = request.method
        status = getattr(response, "status_code", 0)

        logger.info(
            "%s %s -> %s %.2fms",
            method,
            path,
            status,
            elapsed_ms,
        )
        return response
