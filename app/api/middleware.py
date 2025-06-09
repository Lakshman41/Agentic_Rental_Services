# File: agentic_rental_platform/app/api/middleware.py
import time
import uuid
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from app.core.logging import logger

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        client_host = request.client.host if request.client else "unknown_host"
        client_port = request.client.port if request.client else "unknown_port"
        logger.info(
            f"rid={request_id} REQUEST path={request.url.path} method={request.method} "
            f"client={client_host}:{client_port}"
        )
        start_time = time.time()
        response = None
        try:
            response = await call_next(request)
        except Exception as e:
            process_time = (time.time() - start_time) * 1000
            logger.exception(
                f"rid={request_id} Unhandled exception during request processing path={request.url.path} "
                f"method={request.method} completed_in={process_time:.2f}ms: {e}",
                exc_info=e
            )
            raise e 
        finally:
            process_time = (time.time() - start_time) * 1000
            status_code_log = "N/A"
            if response and hasattr(response, 'status_code'):
                status_code_log = response.status_code
            logger.info(
                f"rid={request_id} RESPONSE path={request.url.path} method={request.method} "
                f"status_code={status_code_log} completed_in={process_time:.2f}ms"
            )
        if response and hasattr(response, 'headers'):
            response.headers["X-Request-ID"] = request_id
        return response if response else Response(content="Internal Server Error after middleware processing", status_code=500)

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        # if request.url.scheme == "https":
        #     response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response