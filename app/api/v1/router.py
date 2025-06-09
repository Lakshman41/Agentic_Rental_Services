# File: agentic_rental_platform/app/api/v1/router.py
from fastapi import APIRouter

# Import individual endpoint routers here as they are re-created
from .endpoints import health
from .endpoints import saved_searches
from .endpoints import auth # Will be added next
# from .endpoints import users # If you have separate user management beyond auth
# from .endpoints import properties 
# ... other v1 endpoint modules

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(health.router, prefix="/health", tags=["V1 Health"])
api_router.include_router(auth.router, prefix="/auth", tags=["V1 Authentication & Users"])
api_router.include_router(saved_searches.router, prefix="/saved-searches", tags=["V1 Saved Searches"])
# api_router.include_router(properties.router, prefix="/properties", tags=["V1 Properties"])
# ... and so on