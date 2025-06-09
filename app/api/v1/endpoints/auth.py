# File: app/api/v1/endpoints/auth.py
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm 
from typing import List
import uuid

from app.core.config import settings
from app.core.logging import logger
from app.core import security 
from app.schemas.token import Token, RefreshTokenRequest 
from app.schemas.user import User as UserSchema, UserCreate # Use UserSchema alias for clarity
from app.api.deps import get_user_service, get_current_active_user, get_current_admin_user
from app.services.user_service import UserService 

router = APIRouter()

@router.post("/login/access-token", response_model=Token, tags=["Authentication"])
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    user_svc: UserService = Depends(get_user_service)
):
    logger.info(f"Login attempt for user: {form_data.username}")
    user_orm = await user_svc.get_user_by_email(email=form_data.username)
    if not user_orm or not security.verify_password(form_data.password, user_orm.hashed_password):
        logger.warning(f"Login failed for {form_data.username}: Incorrect email or password.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password",
        )
    if not user_orm.is_active:
        logger.warning(f"Login failed: User {form_data.username} is inactive.")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    
    access_token = security.create_access_token(subject=str(user_orm.id))
    refresh_token = security.create_refresh_token(subject=str(user_orm.id))
    logger.info(f"Login successful for user: {form_data.username}, user_id: {user_orm.id}")
    return Token(access_token=access_token, refresh_token=refresh_token, token_type="bearer")

@router.post("/users/register", response_model=UserSchema, status_code=status.HTTP_201_CREATED, tags=["Users"])
async def register_new_user(
    user_in: UserCreate,
    user_svc: UserService = Depends(get_user_service)
):
    logger.info(f"Registration attempt for email: {user_in.email}")
    try:
        created_user_orm = await user_svc.create_user(user_in=user_in)
    except ValueError as e: 
        logger.warning(f"User registration failed: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    logger.info(f"User registered successfully: {created_user_orm.email}, ID: {created_user_orm.id}")
    return UserSchema.model_validate(created_user_orm)

@router.get("/users/me", response_model=UserSchema, tags=["Users"])
async def read_users_me(current_user: UserSchema = Depends(get_current_active_user)):
    logger.info(f"Fetching details for current user: {current_user.email}")
    return current_user

@router.post("/login/refresh-token", response_model=Token, tags=["Authentication"])
async def refresh_access_token(
    refresh_token_request: RefreshTokenRequest,
    user_svc: UserService = Depends(get_user_service)
):
    refresh_token_str = refresh_token_request.refresh_token
    logger.info(f"Refresh token attempt with token: {refresh_token_str[:10]}...")
    payload = security.decode_token(refresh_token_str, settings.JWT_REFRESH_SECRET_KEY)
    if not payload or payload.get("type") != "refresh":
        logger.warning("Refresh token invalid or not a refresh token.")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    user_id_str = payload.get("sub")
    if not user_id_str:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token payload")
    try:
        user_id = uuid.UUID(user_id_str)
    except (ValueError, TypeError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user ID in refresh token")

    user_orm = await user_svc.get_user_by_id(user_id=user_id)
    if not user_orm or not user_orm.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user for refresh token")
    
    new_access_token = security.create_access_token(subject=str(user_orm.id))
    logger.info(f"Access token refreshed for user: {user_orm.email}, user_id: {user_orm.id}")
    return Token(access_token=new_access_token, token_type="bearer")

@router.get("/users/all", response_model=List[UserSchema], tags=["Admin"])
async def read_all_users(
    skip: int = 0,
    limit: int = 10,
    user_svc: UserService = Depends(get_user_service),
    current_admin: UserSchema = Depends(get_current_admin_user) # RBAC
):
    logger.info(f"Admin {current_admin.email} request to fetch all users. Skip: {skip}, Limit: {limit}")
    users_orm_list = await user_svc.get_users(skip=skip, limit=limit)
    return [UserSchema.model_validate(user_db) for user_db in users_orm_list]

@router.post("/users/me/request-export", status_code=status.HTTP_202_ACCEPTED, tags=["GDPR"])
async def request_user_data_export(
    current_user: UserSchema = Depends(get_current_active_user),
    # background_tasks: BackgroundTasks = Depends() # If using BackgroundTasks
):
    logger.info(f"User {current_user.email} requested data export.")
    # background_tasks.add_task(some_export_function, current_user.id)
    return {"message": "Your data export request has been received."}

@router.delete("/users/me/delete-account", status_code=status.HTTP_202_ACCEPTED, tags=["GDPR"])
async def request_account_deletion(
    current_user: UserSchema = Depends(get_current_active_user),
    user_svc: UserService = Depends(get_user_service),
    # background_tasks: BackgroundTasks = Depends() # If using BackgroundTasks
):
    logger.info(f"User {current_user.email} requested account deletion.")
    await user_svc.deactivate_user(user_id=current_user.id) # Use service method
    # background_tasks.add_task(process_full_deletion, current_user.id)
    return {"message": "Your account deletion request has been received."}