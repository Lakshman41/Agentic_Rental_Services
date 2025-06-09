# File: app/api/deps.py
from typing import Optional, List 
import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import security # For token decoding
from app.core.config import settings
from app.core.logging import logger
# from app.schemas.token import TokenPayload # Not directly used in this file's functions, but often related
from app.schemas.user import User as UserSchema # Pydantic model for user response (aliased for clarity)

from app.core.database import get_db_session # DB session dependency
from app.services.user_service import UserService
from app.services.saved_search_service import SavedSearchService
from app.services.property_service import PropertyService
# from app.models.user import User as UserModel # UserModel is an internal detail of UserService

# OAuth2PasswordBearer tells FastAPI where to look for the token (Authorization: Bearer <token>)
# tokenUrl should point to your login endpoint for Swagger UI's "Authorize" button functionality.
reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login/access-token"
)

# --- Service Dependencies ---

def get_user_service(
    db_session: AsyncSession = Depends(get_db_session)
) -> UserService:
    """Dependency to get an instance of UserService."""
    return UserService(db_session=db_session)

def get_saved_search_service(
    db_session: AsyncSession = Depends(get_db_session)
) -> SavedSearchService:
    """Dependency to get an instance of SavedSearchService."""
    return SavedSearchService(db_session=db_session)

# --- Current User Dependencies ---

async def get_current_user(
    token: str = Depends(reusable_oauth2),
    user_svc: UserService = Depends(get_user_service) 
) -> UserSchema: # Returns Pydantic User schema
    """
    Dependency to get the current user from a token.
    Raises HTTPException if token is invalid or user not found/valid.
    """
    logger.debug(f"Attempting to get current user from token: {token[:10]}...")
    
    payload = security.decode_token(token, settings.JWT_SECRET_KEY)
    if not payload:
        logger.warning("Token decoding failed or token is invalid.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials (invalid token)",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token_type = payload.get("type")
    if token_type != "access":
        logger.warning(f"Invalid token type: {token_type}. Expected 'access'.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id_str = payload.get("sub")
    if not user_id_str:
        logger.warning("Token payload missing 'sub' (subject/user_id).")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials (missing user ID in token)",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        user_id = uuid.UUID(user_id_str)
    except (ValueError, TypeError):
        logger.warning(f"Invalid user ID format in token: {user_id_str}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials (invalid user ID format)",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_orm_model = await user_svc.get_user_by_id(user_id=user_id) 
    if not user_orm_model:
        logger.warning(f"User with ID {user_id} from token not found in database via service.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found", 
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    current_user_pydantic = UserSchema.model_validate(user_orm_model)
    logger.info(f"Current user identified via service: {current_user_pydantic.email} (ID: {current_user_pydantic.id})")
    return current_user_pydantic


async def get_current_active_user(
    current_user: UserSchema = Depends(get_current_user)
) -> UserSchema:
    """
    Dependency to get the current active user.
    Uses get_current_user and then checks if the user is active.
    """
    if not current_user.is_active:
        logger.warning(f"User {current_user.email} is inactive.")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    logger.info(f"Current active user confirmed: {current_user.email}")
    return current_user

# --- Role-Based Access Control (RBAC) Dependencies ---

def require_role(required_role: str):
    """
    Dependency generator that creates a dependency to check for a specific role.
    """
    async def role_checker(current_user: UserSchema = Depends(get_current_active_user)) -> UserSchema:
        logger.debug(f"Role check for user {current_user.email}. Required: {required_role}. User has: {current_user.role}")
        if not current_user.role: # Should not happen if role has a default in model/schema
            logger.warning(f"User {current_user.email} has no role assigned in schema.")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User role not assigned.",
            )
        if current_user.role != required_role:
            logger.warning(f"User {current_user.email} (Role: {current_user.role}) does not have required role: {required_role}.")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Not enough permissions. Requires role: {required_role}.",
            )
        logger.info(f"User {current_user.email} has required role: {required_role}")
        return current_user
    return role_checker

def require_roles(required_roles: List[str]): # Ensure List is imported from typing
    """
    Dependency generator that creates a dependency to check if user has ANY of the specific roles.
    """
    async def roles_checker(current_user: UserSchema = Depends(get_current_active_user)) -> UserSchema:
        logger.debug(f"Roles check for user {current_user.email}. Required (any of): {required_roles}. User has: {current_user.role}")
        if not current_user.role:
            logger.warning(f"User {current_user.email} has no role assigned in schema.")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User role not assigned.",
            )
        if current_user.role not in required_roles:
            logger.warning(f"User {current_user.email} (Role: {current_user.role}) does not have any of the required roles: {required_roles}.")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Not enough permissions. Requires one of roles: {', '.join(required_roles)}.",
            )
        logger.info(f"User {current_user.email} has one of the required roles. Role: {current_user.role}")
        return current_user
    return roles_checker

def get_property_service( # <--- ADD THIS FUNCTION
    db_session: AsyncSession = Depends(get_db_session)
) -> PropertyService:
    """Dependency to get an instance of PropertyService."""
    return PropertyService(db_session=db_session)

# Specific role dependencies (examples)
get_current_admin_user = require_role("admin")
get_current_agent_user = require_role("agent")
# Example of a dependency requiring one of multiple roles:
# get_current_privileged_user = require_roles(["admin", "agent"])