# File: app/services/saved_search_service.py
from typing import List, Optional, Dict, Any
import uuid

from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload # If SavedSearch has eager-loaded relationships

from app.core.logging import logger
from app.models.saved_search import SavedSearch as SavedSearchModel
from app.schemas.search import SavedSearchCreate, SavedSearchUpdate # Pydantic schemas

class SavedSearchService:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def create_saved_search(
        self, *, user_id: uuid.UUID, search_in: SavedSearchCreate
    ) -> SavedSearchModel:
        """
        Creates a new saved search for a user.
        """
        logger.info(f"User {user_id} creating saved search: {search_in.name}")
        
        # The search_criteria from Pydantic model needs to be converted to a dict for JSONB
        search_criteria_dict = search_in.search_criteria.model_dump(exclude_none=True)

        db_saved_search = SavedSearchModel(
            user_id=user_id,
            name=search_in.name,
            search_criteria=search_criteria_dict
            # id, created_at, updated_at are handled by the model/DB
        )
        self.db_session.add(db_saved_search)
        await self.db_session.commit()
        await self.db_session.refresh(db_saved_search)
        logger.info(f"Saved search '{db_saved_search.name}' (ID: {db_saved_search.id}) created for user {user_id}.")
        return db_saved_search

    async def get_saved_search_by_id(
        self, *, user_id: uuid.UUID, saved_search_id: uuid.UUID
    ) -> Optional[SavedSearchModel]:
        """
        Retrieves a specific saved search by its ID, ensuring it belongs to the user.
        """
        logger.debug(f"User {user_id} fetching saved search by ID: {saved_search_id}")
        statement = (
            select(SavedSearchModel)
            .where(SavedSearchModel.id == saved_search_id)
            .where(SavedSearchModel.user_id == user_id)
            # .options(selectinload(SavedSearchModel.user)) # If you want to eager load user
        )
        result = await self.db_session.execute(statement)
        saved_search = result.scalar_one_or_none()

        if saved_search:
            logger.info(f"Saved search found for user {user_id}: {saved_search.name} (ID: {saved_search.id})")
        else:
            logger.warning(f"Saved search ID {saved_search_id} not found or not owned by user {user_id}.")
        return saved_search

    async def list_saved_searches_by_user(
        self, *, user_id: uuid.UUID, skip: int = 0, limit: int = 100
    ) -> List[SavedSearchModel]:
        """
        Lists all saved searches for a given user with pagination.
        """
        logger.debug(f"User {user_id} listing saved searches. Skip: {skip}, Limit: {limit}")
        statement = (
            select(SavedSearchModel)
            .where(SavedSearchModel.user_id == user_id)
            .order_by(SavedSearchModel.created_at.desc()) # Or by name, etc.
            .offset(skip)
            .limit(limit)
        )
        result = await self.db_session.execute(statement)
        saved_searches = list(result.scalars().all())
        logger.info(f"Found {len(saved_searches)} saved searches for user {user_id}.")
        return saved_searches

    async def update_saved_search(
        self, *, user_id: uuid.UUID, saved_search_id: uuid.UUID, search_in: SavedSearchUpdate
    ) -> Optional[SavedSearchModel]:
        """
        Updates an existing saved search for a user.
        """
        logger.info(f"User {user_id} updating saved search ID: {saved_search_id} with data: {search_in.model_dump(exclude_unset=True)}")
        
        db_saved_search = await self.get_saved_search_by_id(user_id=user_id, saved_search_id=saved_search_id)
        if not db_saved_search:
            return None # Not found or not owned by user

        update_data = search_in.model_dump(exclude_unset=True) # Get only fields that were set
        
        if "name" in update_data:
            db_saved_search.name = update_data["name"]
        if "search_criteria" in update_data and update_data["search_criteria"] is not None:
            # search_in.search_criteria is PropertySearchFilters Pydantic model
            db_saved_search.search_criteria = update_data["search_criteria"] # Pydantic model_dump handles this
            # If search_in.search_criteria was a dict already:
            # db_saved_search.search_criteria = update_data["search_criteria"]

        # updated_at will be handled by the model's onupdate
        self.db_session.add(db_saved_search)
        await self.db_session.commit()
        await self.db_session.refresh(db_saved_search)
        logger.info(f"Saved search ID {saved_search_id} updated for user {user_id}.")
        return db_saved_search

    async def delete_saved_search(
        self, *, user_id: uuid.UUID, saved_search_id: uuid.UUID
    ) -> bool:
        """
        Deletes a saved search for a user. Returns True if deleted, False otherwise.
        """
        logger.info(f"User {user_id} attempting to delete saved search ID: {saved_search_id}")
        
        # First, ensure the saved search exists and belongs to the user
        db_saved_search = await self.get_saved_search_by_id(user_id=user_id, saved_search_id=saved_search_id)
        if not db_saved_search:
            logger.warning(f"Delete failed: Saved search ID {saved_search_id} not found or not owned by user {user_id}.")
            return False

        # Perform the delete operation
        # statement = delete(SavedSearchModel).where(SavedSearchModel.id == saved_search_id).where(SavedSearchModel.user_id == user_id)
        # result = await self.db_session.execute(statement)
        # await self.db_session.commit()
        # if result.rowcount > 0: ...
        
        # Simpler: delete the object if fetched
        await self.db_session.delete(db_saved_search)
        await self.db_session.commit()
        
        logger.info(f"Saved search ID {saved_search_id} deleted for user {user_id}.")
        return True