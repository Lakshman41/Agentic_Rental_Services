# File: app/api/v1/endpoints/saved_searches.py
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query

from app.core.logging import logger
from app.schemas.search import (
    SavedSearch, 
    SavedSearchCreate, 
    SavedSearchUpdate
)
from app.schemas.user import User as UserSchema # For current_user type hint
from app.services.saved_search_service import SavedSearchService
from app.api.deps import get_current_active_user, get_user_service # Assuming get_user_service provides UserService
# We need a way to get SavedSearchService, similar to UserService
from app.api.deps import get_db_session # Import get_db_session
from sqlalchemy.ext.asyncio import AsyncSession # Import AsyncSession for type hint

router = APIRouter()

# Dependency to get an instance of SavedSearchService
def get_saved_search_service(
    db_session: AsyncSession = Depends(get_db_session)
) -> SavedSearchService:
    return SavedSearchService(db_session=db_session)


@router.post("/", response_model=SavedSearch, status_code=status.HTTP_201_CREATED, summary="Create a new saved search")
async def create_new_saved_search(
    *,
    search_in: SavedSearchCreate,
    saved_search_svc: SavedSearchService = Depends(get_saved_search_service),
    current_user: UserSchema = Depends(get_current_active_user)
):
    """
    Create a new saved search for the authenticated user.
    - **name**: A user-friendly name for the search.
    - **search_criteria**: The detailed search filter object.
    """
    logger.info(f"User {current_user.email} (ID: {current_user.id}) creating saved search: {search_in.name}")
    saved_search_db = await saved_search_svc.create_saved_search(
        user_id=current_user.id, search_in=search_in
    )
    # Convert ORM model to Pydantic schema for response
    return SavedSearch.model_validate(saved_search_db)


@router.get("/", response_model=List[SavedSearch], summary="List user's saved searches")
async def list_my_saved_searches(
    *,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    saved_search_svc: SavedSearchService = Depends(get_saved_search_service),
    current_user: UserSchema = Depends(get_current_active_user)
):
    """
    Retrieve a list of saved searches for the authenticated user.
    """
    logger.info(f"User {current_user.email} (ID: {current_user.id}) listing saved searches. Skip: {skip}, Limit: {limit}")
    saved_searches_db = await saved_search_svc.list_saved_searches_by_user(
        user_id=current_user.id, skip=skip, limit=limit
    )
    return [SavedSearch.model_validate(ss) for ss in saved_searches_db]


@router.get("/{saved_search_id}", response_model=SavedSearch, summary="Get a specific saved search")
async def get_specific_saved_search(
    *,
    saved_search_id: uuid.UUID,
    saved_search_svc: SavedSearchService = Depends(get_saved_search_service),
    current_user: UserSchema = Depends(get_current_active_user)
):
    """
    Retrieve a specific saved search by its ID for the authenticated user.
    """
    logger.info(f"User {current_user.email} (ID: {current_user.id}) retrieving saved search ID: {saved_search_id}")
    saved_search_db = await saved_search_svc.get_saved_search_by_id(
        user_id=current_user.id, saved_search_id=saved_search_id
    )
    if not saved_search_db:
        logger.warning(f"Saved search ID {saved_search_id} not found for user {current_user.email} (ID: {current_user.id}).")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Saved search not found")
    return SavedSearch.model_validate(saved_search_db)


@router.put("/{saved_search_id}", response_model=SavedSearch, summary="Update a saved search")
async def update_existing_saved_search(
    *,
    saved_search_id: uuid.UUID,
    search_in: SavedSearchUpdate,
    saved_search_svc: SavedSearchService = Depends(get_saved_search_service),
    current_user: UserSchema = Depends(get_current_active_user)
):
    """
    Update an existing saved search for the authenticated user.
    Only provided fields will be updated.
    """
    logger.info(f"User {current_user.email} (ID: {current_user.id}) updating saved search ID: {saved_search_id}")
    updated_saved_search_db = await saved_search_svc.update_saved_search(
        user_id=current_user.id, saved_search_id=saved_search_id, search_in=search_in
    )
    if not updated_saved_search_db:
        logger.warning(f"Update failed: Saved search ID {saved_search_id} not found for user {current_user.email} (ID: {current_user.id}).")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Saved search not found")
    return SavedSearch.model_validate(updated_saved_search_db)


@router.delete("/{saved_search_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a saved search")
async def delete_existing_saved_search(
    *,
    saved_search_id: uuid.UUID,
    saved_search_svc: SavedSearchService = Depends(get_saved_search_service),
    current_user: UserSchema = Depends(get_current_active_user)
):
    """
    Delete a specific saved search by its ID for the authenticated user.
    Returns 204 No Content on successful deletion.
    """
    logger.info(f"User {current_user.email} (ID: {current_user.id}) deleting saved search ID: {saved_search_id}")
    deleted = await saved_search_svc.delete_saved_search(
        user_id=current_user.id, saved_search_id=saved_search_id
    )
    if not deleted:
        logger.warning(f"Delete failed: Saved search ID {saved_search_id} not found for user {current_user.email} (ID: {current_user.id}).")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Saved search not found")
    # No content to return for 204
    return Response(status_code=status.HTTP_204_NO_CONTENT)