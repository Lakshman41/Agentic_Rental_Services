# File: agentic_rental_platform/app/api/v1/endpoints/properties.py
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query

from app.core.logging import logger
from app.schemas.property import Property as PropertySchema, PropertyList
from app.schemas.search import PropertySearchFilters
from app.services.property_service import PropertyService
# Import service getter from deps
from app.api.deps import get_property_service, get_current_active_user # get_current_active_user for future CRUD
from app.schemas.user import User as UserSchema # For current_user type hint

router = APIRouter()

# The get_property_service dependency should be defined in app/api/deps.py
# We import it from there.

@router.post("/search", response_model=PropertyList, summary="Search for properties")
async def search_properties_endpoint(
    search_filters_query: PropertySearchFilters = Depends(), 
    property_svc: PropertyService = Depends(get_property_service)
):
    logger.info(f"Received property search request with filters: {search_filters_query.model_dump(exclude_none=True)}")
    try:
        properties_orm_list, total_count = await property_svc.search_properties(
            filters=search_filters_query
        )
    except Exception as e:
        logger.error(f"Error during property search: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while searching for properties."
        )
    property_schemas = [PropertySchema.model_validate(prop_orm) for prop_orm in properties_orm_list]
    return PropertyList(
        items=property_schemas,
        total=total_count,
        page=search_filters_query.page,
        size=search_filters_query.size
    )

@router.get("/{property_id}", response_model=PropertySchema, summary="Get a specific property by ID")
async def get_property_details(
    property_id: uuid.UUID,
    property_svc: PropertyService = Depends(get_property_service)
):
    logger.info(f"Fetching details for property ID: {property_id}")
    property_orm = await property_svc.get_property_by_id(property_id=property_id)
    if not property_orm:
        logger.warning(f"Property ID {property_id} not found.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")
    
    if not property_orm.is_published and property_orm.archived_at is None:
        logger.warning(f"Attempt to access unpublished property ID {property_id}.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found or not available")
    return PropertySchema.model_validate(property_orm)

# --- Placeholder CRUD Endpoints for Property Management (will require authentication and authorization) ---
# @router.post("/", response_model=PropertySchema, status_code=status.HTTP_201_CREATED, summary="Create a new property")
# async def create_new_property(
#     *,
#     property_in: PropertyCreate, # Defined in app.schemas.property
#     property_svc: PropertyService = Depends(get_property_service),
#     current_user: UserSchema = Depends(get_current_active_user) # User must be authenticated
# ):
#     # Add authorization logic: e.g., only users with 'owner' or 'agent' role can create
#     # if current_user.role not in ["owner", "agent", "admin"]:
#     #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to create properties")
#     logger.info(f"User {current_user.email} creating property: {property_in.title}")
#     # The service method will need owner_id (current_user.id)
#     # property_db = await property_svc.create_property(property_in=property_in, owner_id=current_user.id)
#     # return PropertySchema.model_validate(property_db)
#     raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Property creation not yet implemented")

# @router.put("/{property_id}", response_model=PropertySchema, summary="Update a property")
# async def update_existing_property(...):
#     # Check ownership or admin role before allowing update
#     raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Property update not yet implemented")

# @router.delete("/{property_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a property")
# async def delete_existing_property(...):
#     # Check ownership or admin role before allowing delete
#     raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Property deletion not yet implemented")