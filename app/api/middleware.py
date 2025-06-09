# File: agentic_rental_platform/app/api/middleware.py
import time
import uuid
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from app.core.logging import logger # Our configured logger

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = str(uuid.uuid4())
        
        # Add request_id to request state so it can be accessed in endpoints if needed
        request.state.request_id = request_id

        # Log request details
        # Client IP might be behind a proxy, consider X-Forwarded-For if applicable and trusted
        client_host = request.client.host if request.client else "unknown_host"
        client_port = request.client.port if request.client else "unknown_port"
        
        logger.info(
            f"rid={request_id} REQUEST path={request.url.path} method={request.method} "
            f"client={client_host}:{client_port}"
        )
        
        start_time = time.time()
        response = None # Initialize response
        try:
            response = await call_next(request)
        except Exception as e:
            # This will log exceptions that occur before FastAPI's own exception handlers
            # or if an exception is not an HTTPException and bubbles up this far.
            process_time = (time.time() - start_time) * 1000
            logger.exception(
                f"rid={request_id} Unhandled exception during request processing path={request.url.path} "
                f"method={request.method} completed_in={process_time:.2f}ms: {e}",
                exc_info=e # Includes stack trace
            )
            # Re-raise the exception to be handled by FastAPI's main error handlers or custom handlers
            raise e 
        finally:
            # This block executes whether an exception occurred or not.
            process_time = (time.time() - start_time) * 1000
            
            status_code_log = "N/A" # Default if response object isn't fully formed (e.g. early client disconnect)
            if response and hasattr(response, 'status_code'):
                status_code_log = response.status_code
            
            logger.info(
                f"rid={request_id} RESPONSE path={request.url.path} method={request.method} "
                f"status_code={status_code_log} completed_in={process_time:.2f}ms"
            )

        # Ensure X-Request-ID header is added even if an exception was handled by call_next
        # and a valid response object was formed.
        if response and hasattr(response, 'headers'):
            response.headers["X-Request-ID"] = request_id
        
        return response if response else Response(content="Internal Server Error after middleware processing", status_code=500)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        # Content-Security-Policy is powerful but needs careful configuration. Start restrictive.
        # response.headers["Content-Security-Policy"] = "default-src 'self'; img-src *; style-src 'self' 'unsafe-inline'; script-src 'self'"
        # Strict-Transport-Security - only if your app is always served over HTTPS
        # if request.url.scheme == "https": # Or check a config flag
        #     response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["X-XSS-Protection"] = "1; mode=block" # Deprecated by CSP, but adds layer for older browsers
        # Referrer-Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response

# Potential future middleware:
# - RateLimitingMiddleware
# - DatabaseSessionMiddleware (though we use Depends for sessions now)