import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)

LOG_FORMAT = "%s %s → %d (%sms)"
MS_FACTOR = 1000.0
DECIMAL_PLACES = 1


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        start_time = time.perf_counter()
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - start_time) * MS_FACTOR, DECIMAL_PLACES)
        logger.info(
            LOG_FORMAT,
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )
        return response
