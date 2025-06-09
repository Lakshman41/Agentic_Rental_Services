# File: agentic_rental_platform/app/main.py
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError, HTTPException as FastAPIHTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import asyncio

from app.core.config import settings
from app.core.logging import logger
from app.api.middleware import LoggingMiddleware, SecurityHeadersMiddleware
from app.api.v1.router import api_router as api_v1_router

app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    version="0.1.0",
    description="Backend for Agentic Rental Services Platform",
)

logger.info("Registering LoggingMiddleware.")
app.add_middleware(LoggingMiddleware)
logger.info("Registering SecurityHeadersMiddleware.")
app.add_middleware(SecurityHeadersMiddleware)

if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin).rstrip('/') for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    logger.info(f"CORS middleware enabled for origins: {settings.BACKEND_CORS_ORIGINS}")
else:
    logger.warning("CORS middleware NOT enabled (BACKEND_CORS_ORIGINS not set or empty).")

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    error_details = exc.errors()
    logger.error(f"Validation error for request {request.method} {request.url}: {error_details}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Validation Error", "errors": error_details},
    )

@app.exception_handler(FastAPIHTTPException)
async def http_exception_handler(request: Request, exc: FastAPIHTTPException):
    logger.error(
        f"HTTPException for request {request.method} {request.url}: "
        f"Status Code: {exc.status_code}, Detail: {exc.detail}"
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=exc.headers,
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.exception(
        f"Unhandled exception for request {request.method} {request.url}", 
        exc_info=exc
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred.", "error_type": type(exc).__name__},
    )

logger.info(f"Including API router for v1 at prefix: {settings.API_V1_STR}")
app.include_router(api_v1_router, prefix=settings.API_V1_STR)

@app.get("/", tags=["Health Check"], summary="Root health check endpoint")
async def root():
    logger.info("Root health check endpoint was called.")
    return {
        "status": "ok",
        "message": f"Welcome to {settings.APP_NAME}!",
        "version": app.version,
        "environment": settings.ENVIRONMENT,
        "debug_mode": settings.DEBUG
    }

@app.on_event("startup")
async def startup_event():
    logger.info(f"Application startup: {settings.APP_NAME} v{app.version} (Env: {settings.ENVIRONMENT}, Debug: {settings.DEBUG})")
    # Database engine is created at import time in app.core.database
    # Any other async initializations can go here.
    logger.info("Application startup complete.")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Application shutdown initiated.")
    logger.info("Application shutdown complete.")

if __name__ == "__main__":
    import uvicorn
    logger.info(f"Starting Uvicorn server directly for {settings.APP_NAME}...")
    uvicorn.run(
        "app.main:app", 
        host="0.0.0.0", 
        port=8000, 
        log_level=settings.LOG_LEVEL.lower(),
        reload=True
    )