# File: agentic_rental_platform/app/api/v1/endpoints/health.py
from fastapi import APIRouter
from app.core.config import settings
from app.core.logging import logger

router = APIRouter()

@router.get("/", summary="API v1 Health Check", tags=["V1 Health"])
async def health_check_v1():
    """
    Health check for API version 1.
    """
    logger.info(f"API v1 health check endpoint called for {settings.APP_NAME}.")
    return {
        "status": "ok",
        "message": f"API v1 is healthy for {settings.APP_NAME}",
        "version": "v1",
        "environment": settings.ENVIRONMENT
    }