# File: agentic_rental_platform/app/services/property_service.py
from typing import List, Optional, Dict, Any, Tuple
import uuid
import math 

from sqlalchemy import select, func, text, literal_column, or_ # Added or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.logging import logger
from app.models.property import Property as PropertyModel
# from app.models.property_embedding import PropertyEmbedding as PropertyEmbeddingModel # For semantic search later
from app.schemas.search import PropertySearchFilters
# from sentence_transformers import SentenceTransformer # For semantic search later

EARTH_RADIUS_KM = 6371.0

class PropertyService:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
        # self.embedding_model = None # Initialize later for semantic search

    # _haversine function as defined before (keep it)
    async def _haversine(self, lat1, lon1, lat2, lon2):
        lon1, lat1, lon2, lat2 = map(math.radians, [lon1, lat1, lon2, lat2])
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
        c = 2 * math.asin(math.sqrt(a))
        distance = EARTH_RADIUS_KM * c
        return distance

    async def search_properties(
        self, filters: PropertySearchFilters
    ) -> Tuple[List[PropertyModel], int]:
        logger.info(f"Property search with filters: {filters.model_dump(exclude_none=True)}")

        # --- 1. Build Base Query for Structured Filters ---
        query = select(PropertyModel).options(
            selectinload(PropertyModel.owner), # Eager load owner
            selectinload(PropertyModel.images)  # Eager load images
        )

        # --- Apply Structured Filters ---
        if filters.city:
            query = query.where(PropertyModel.city.ilike(f"%{filters.city}%"))
        if filters.state_province:
            query = query.where(PropertyModel.state_province.ilike(f"%{filters.state_province}%"))
        if filters.postal_code:
            query = query.where(PropertyModel.postal_code == filters.postal_code)
        if filters.property_type:
            # If property_type could be a list: query = query.where(PropertyModel.property_type.in_(filters.property_type_list))
            query = query.where(PropertyModel.property_type.ilike(f"%{filters.property_type}%"))
        
        if filters.min_bedrooms is not None:
            query = query.where(PropertyModel.num_bedrooms >= filters.min_bedrooms)
        if filters.max_bedrooms is not None:
            query = query.where(PropertyModel.num_bedrooms <= filters.max_bedrooms)
        
        if filters.min_bathrooms is not None:
            query = query.where(PropertyModel.num_bathrooms >= filters.min_bathrooms)
        if filters.max_bathrooms is not None:
            query = query.where(PropertyModel.num_bathrooms <= filters.max_bathrooms)

        if filters.min_area_sqft is not None:
            query = query.where(PropertyModel.area_sqft >= filters.min_area_sqft)
        if filters.max_area_sqft is not None:
            query = query.where(PropertyModel.area_sqft <= filters.max_area_sqft)
            
        if filters.min_rent_price is not None:
            query = query.where(PropertyModel.rent_price >= filters.min_rent_price)
        if filters.max_rent_price is not None:
            query = query.where(PropertyModel.rent_price <= filters.max_rent_price)
        if filters.rent_price_period:
            query = query.where(PropertyModel.rent_price_period.ilike(f"%{filters.rent_price_period}%"))

        if filters.available_from:
            query = query.where(
                or_( # Use or_ for multiple conditions on availability_date
                    PropertyModel.availability_date == None, # Always available if no date set
                    PropertyModel.availability_date >= filters.available_from
                )
            )
        # Note: filters.available_until is not yet implemented here. Would be another clause.

        # TODO: Implement filters.required_amenities (likely involves JSONB operations if amenities are stored in JSON)
        # Example for JSONB (PostgreSQL specific, requires amenities to be a dict):
        # if filters.required_amenities:
        #     for amenity_key in filters.required_amenities:
        #         # This checks if the key exists and is true, or if it's a specific string value
        #         # Adjust based on how your amenities are structured
        #         query = query.where(
        #             or_(
        #                 PropertyModel.amenities[amenity_key].astext == 'true', # For boolean true
        #                 PropertyModel.amenities.has_key(amenity_key) # If just existence of key matters
        #             )
        #         )


        # Always filter for published and not archived properties for general searches
        query = query.where(PropertyModel.is_published == True)
        query = query.where(PropertyModel.archived_at == None)

        # --- 2. Count Total Matching Properties (before pagination) ---
        # Important: clone the query for counting before applying limit/offset or location post-filter
        count_subquery = query.order_by(None).alias("count_subquery") # Remove ordering for count
        count_query = select(func.count()).select_from(count_subquery)
        
        total_count_result = await self.db_session.execute(count_query)
        total_count = total_count_result.scalar_one()
        
        if total_count == 0:
            logger.info("No properties found matching structured filters.")
            return [], 0

        # --- 3. Apply Sorting ---
        if filters.sort_by:
            if filters.sort_by == "rent_price_asc":
                query = query.order_by(PropertyModel.rent_price.asc())
            elif filters.sort_by == "rent_price_desc":
                query = query.order_by(PropertyModel.rent_price.desc())
            elif filters.sort_by == "date_posted_desc":
                query = query.order_by(PropertyModel.created_at.desc())
            # Add more sort options later (e.g., 'relevance' for semantic search)
        else:
            # Default sort if nothing specified
            query = query.order_by(PropertyModel.created_at.desc()) # Default sort
            
        # --- 4. Apply Pagination ---
        query = query.offset((filters.page - 1) * filters.size).limit(filters.size)

        # Execute the main query to get property ORM objects
        results = await self.db_session.execute(query)
        properties_orm: List[PropertyModel] = list(results.scalars().unique().all())

        # --- 5. Location Radius Filter (Post-DB Haversine - applied after pagination) ---
        # This will filter the current page of results.
        # For accurate total_count with radius, radius filter must be in the DB query.
        final_properties_list = properties_orm
        if filters.location and properties_orm:
            logger.debug(f"Applying location radius filter (post-DB): {filters.location}")
            center_lat = filters.location.latitude
            center_lon = filters.location.longitude
            radius_km = filters.location.radius_km
            
            properties_within_radius: List[PropertyModel] = []
            for prop in properties_orm:
                if prop.latitude is not None and prop.longitude is not None:
                    distance = await self._haversine(center_lat, center_lon, prop.latitude, prop.longitude)
                    if distance <= radius_km:
                        properties_within_radius.append(prop)
            final_properties_list = properties_within_radius
            # Note: total_count is still for pre-radius filtering.
            # The number of items returned might be less than 'size' due to this post-filter.

        logger.info(f"Search returned {len(final_properties_list)} properties for page {filters.page} (total matching structured filters before radius/pagination: {total_count}).")
        return final_properties_list, total_count

    # get_property_by_id method as defined before (keep it)
    async def get_property_by_id(self, property_id: uuid.UUID) -> Optional[PropertyModel]:
        logger.debug(f"Fetching property by ID: {property_id}")
        stmt = (
            select(PropertyModel)
            .where(PropertyModel.id == property_id)
            .options(
                selectinload(PropertyModel.owner), 
                selectinload(PropertyModel.images),
                # selectinload(PropertyModel.embedding) # Optional
            )
        )
        result = await self.db_session.execute(stmt)
        property_orm = result.scalar_one_or_none()
        if property_orm:
            logger.info(f"Property found: {property_orm.title}")
            if not property_orm.is_published and property_orm.archived_at is None:
                 logger.info(f"Property {property_id} is not published.")
                 # Decide here if service layer should return unpublished items or if API layer handles this
        else:
            logger.warning(f"Property with ID {property_id} not found.")
        return property_orm

    # TODO: Implement create_property, update_property, delete_property
    # async def create_property(self, property_in: PropertyCreate, owner_id: uuid.UUID) -> PropertyModel: ...