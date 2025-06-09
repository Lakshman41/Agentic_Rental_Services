# File: app/services/property_service.py
from typing import List, Optional, Dict, Any, Tuple
import uuid
import math # For haversine distance calculation

from sqlalchemy import select, func, text, literal_column # Add literal_column
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload # For eager loading relationships

from app.core.logging import logger
from app.models.property import Property as PropertyModel
from app.models.property_embedding import PropertyEmbedding as PropertyEmbeddingModel
from app.schemas.search import PropertySearchFilters
from app.schemas.property import Property as PropertySchema, PropertyList # For response
# from sentence_transformers import SentenceTransformer # We'll add this when implementing semantic search

# Placeholder for SentenceTransformer model - load once ideally
# EMBEDDING_MODEL_NAME = 'all-MiniLM-L6-v2' # or your chosen model
# embedding_model = None 
# try:
#     # embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
#     logger.info(f"SentenceTransformer model '{EMBEDDING_MODEL_NAME}' loaded for PropertyService.")
# except Exception as e:
#     logger.error(f"Failed to load SentenceTransformer model '{EMBEDDING_MODEL_NAME}': {e}")
#     # Handle appropriately, maybe SearchAgent cannot do semantic search

# Earth radius in kilometers for Haversine
EARTH_RADIUS_KM = 6371.0

class PropertyService:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
        # In a real app, the embedding model might be passed in or accessed via a singleton service
        # self.embedding_model = embedding_model 

    async def _haversine(self, lat1, lon1, lat2, lon2):
        """
        Calculate the great circle distance between two points
        on the earth (specified in decimal degrees)
        """
        # Convert decimal degrees to radians
        lon1, lat1, lon2, lat2 = map(math.radians, [lon1, lat1, lon2, lat2])

        # Haversine formula
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
        c = 2 * math.asin(math.sqrt(a))
        distance = EARTH_RADIUS_KM * c
        return distance

    async def search_properties(
        self, filters: PropertySearchFilters
    ) -> Tuple[List[PropertyModel], int]: # Returns list of ORM models and total count
        """
        Searches for properties based on various filters, including semantic and location.
        """
        logger.info(f"Property search initiated with filters: {filters.model_dump(exclude_none=True)}")

        # --- 1. Semantic Search (if query is provided) ---
        semantic_property_ids: Optional[List[uuid.UUID]] = None
        # if filters.query and self.embedding_model:
        #     try:
        #         logger.debug(f"Performing semantic search for query: '{filters.query}'")
        #         query_embedding_list = self.embedding_model.encode(filters.query).tolist()
        #         query_embedding_str = str(query_embedding_list) # For pgvector SQL
                
        #         # pgvector distance operators:
        #         # <-> l2_distance
        #         # <=> cosine_distance (1 - cosine_similarity, smaller is better)
        #         # <#> inner_product (negative for similarity if normalized, larger is better)
        #         # We indexed with vector_cosine_ops, so use <=>
        #         # Limit initial semantic results to a reasonable number, e.g., 100-200, before other filters
        #         # This limit should be configurable.
        #         SEMANTIC_SEARCH_LIMIT = 100 
        #         # Adjust distance threshold as needed; 0.5 for cosine distance is a moderate similarity
        #         # (cosine similarity of 0.5). Smaller distance = more similar.
        #         # MAX_COSINE_DISTANCE = 0.7 # Corresponds to cosine similarity >= 0.3

        #         # text() is used for raw SQL fragments with bind parameters
        #         # Use literal_column for the distance column name to prevent SQL injection if it were dynamic
        #         stmt = (
        #             select(PropertyEmbeddingModel.property_id, 
        #                    literal_column(f"embedding <=> '{query_embedding_str}'").label("distance"))
        #             .order_by(literal_column("distance").asc())
        #             # .where(literal_column(f"embedding <=> '{query_embedding_str}'") < MAX_COSINE_DISTANCE) # Optional threshold
        #             .limit(SEMANTIC_SEARCH_LIMIT)
        #         )
        #         result = await self.db_session.execute(stmt)
        #         # semantic_property_ids = [row.property_id for row in result.all()]
        #         # Using .all() might be inefficient for large result sets before knowing total count
        #         # Instead, let's fetch all property_ids that match semantically up to a limit
        #         semantic_results = result.mappings().all() # list of dict-like row mappings
        #         semantic_property_ids = [row["property_id"] for row in semantic_results]


        #         if not semantic_property_ids:
        #             logger.info("Semantic search yielded no results. Returning empty list.")
        #             return [], 0 
        #         logger.info(f"Semantic search found {len(semantic_property_ids)} potential property IDs.")
        #     except Exception as e:
        #         logger.error(f"Error during semantic search: {e}", exc_info=True)
        #         # Decide behavior: fallback to keyword search, or return error, or empty?
        #         # For now, if semantic search fails, we proceed without semantic filtering.
        #         semantic_property_ids = None 
        # else:
        #     logger.debug("No query for semantic search or embedding model not available.")
        # --- End Semantic Search ---


        # --- 2. Build Base Query for Structured Filters ---
        # Eager load relationships to avoid N+1 queries when accessing owner, images
        query = select(PropertyModel).options(
            selectinload(PropertyModel.owner),
            selectinload(PropertyModel.images),
            # selectinload(PropertyModel.embedding) # Usually not needed in search results list
        )

        # Apply semantic search results as a primary filter if available
        # if semantic_property_ids is not None: # This implies semantic search was attempted
        #     if not semantic_property_ids: # Semantic search ran but found nothing
        #         return [], 0
        #     query = query.where(PropertyModel.id.in_(semantic_property_ids))

        # Apply structured filters
        if filters.city:
            query = query.where(PropertyModel.city.ilike(f"%{filters.city}%"))
        if filters.state_province:
            query = query.where(PropertyModel.state_province.ilike(f"%{filters.state_province}%"))
        if filters.postal_code:
            query = query.where(PropertyModel.postal_code == filters.postal_code)
        if filters.property_type:
            query = query.where(PropertyModel.property_type.ilike(f"%{filters.property_type}%"))
        
        if filters.min_bedrooms is not None:
            query = query.where(PropertyModel.num_bedrooms >= filters.min_bedrooms)
        if filters.max_bedrooms is not None:
            query = query.where(PropertyModel.num_bedrooms <= filters.max_bedrooms)
        if filters.min_bathrooms is not None:
            query = query.where(PropertyModel.num_bathrooms >= filters.min_bathrooms)
        if filters.max_bathrooms is not None:
            query = query.where(PropertyModel.num_bathrooms <= filters.max_bathrooms)
        
        if filters.min_rent_price is not None:
            query = query.where(PropertyModel.rent_price >= filters.min_rent_price)
        if filters.max_rent_price is not None:
            query = query.where(PropertyModel.rent_price <= filters.max_rent_price)
        if filters.rent_price_period:
            query = query.where(PropertyModel.rent_price_period == filters.rent_price_period)

        if filters.available_from:
            # Property must be available on or after this date, or have no specific availability_date (always available)
            query = query.where(
                (PropertyModel.availability_date >= filters.available_from) |
                (PropertyModel.availability_date == None)
            )
        
        # Filter for published properties only for regular user searches
        query = query.where(PropertyModel.is_published == True)
        query = query.where(PropertyModel.archived_at == None) # Exclude soft-deleted

        # --- 3. Count Total Matching Properties (before location radius filter and pagination) ---
        # This count is for all properties matching structured/semantic filters *before* pagination
        # and before fine-grained location radius filtering.
        # We will refine the main query further for location and pagination.
        
        # Create a count query based on the current filtered query
        count_query = select(func.count()).select_from(query.order_by(None).subquery()) # subquery() and order_by(None) for count
        total_count_result = await self.db_session.execute(count_query)
        total_count = total_count_result.scalar_one()
        
        if total_count == 0:
            logger.info("No properties found matching structured/semantic filters.")
            return [], 0

        # --- 4. Apply Sorting (before location radius and pagination for consistency) ---
        # If semantic_property_ids are used, sorting by relevance might be tricky here
        # as the initial semantic query already ordered by distance.
        # For now, simple column-based sorting.
        # if filters.sort_by and not semantic_property_ids: # Don't re-sort if semantic sort already applied
        if filters.sort_by:
            if filters.sort_by == "rent_price_asc":
                query = query.order_by(PropertyModel.rent_price.asc())
            elif filters.sort_by == "rent_price_desc":
                query = query.order_by(PropertyModel.rent_price.desc())
            elif filters.sort_by == "date_posted_desc": # Assuming created_at is date_posted
                query = query.order_by(PropertyModel.created_at.desc())
            # Add more sort options: relevance (if semantic), num_bedrooms etc.
        else:
            # Default sort if nothing specified (e.g., by creation date)
            query = query.order_by(PropertyModel.created_at.desc())
            
        # --- 5. Apply Pagination to the query built so far ---
        query = query.offset((filters.page - 1) * filters.size).limit(filters.size)

        # Execute the main query to get property ORM objects
        results = await self.db_session.execute(query)
        properties_orm: List[PropertyModel] = list(results.scalars().unique().all()) # .unique() to handle eager loads correctly

        # --- 6. Location Radius Filter (if applicable, applied post-DB for non-PostGIS) ---
        # This is a post-filter if not using PostGIS. For large result sets before pagination,
        # this can be inefficient. Ideal is to do radius in DB.
        # if filters.location and properties_orm:
        #     logger.debug(f"Applying location radius filter: {filters.location}")
        #     center_lat = filters.location.latitude
        #     center_lon = filters.location.longitude
        #     radius_km = filters.location.radius_km
            
        #     filtered_by_radius: List[PropertyModel] = []
        #     for prop in properties_orm:
        #         if prop.latitude is not None and prop.longitude is not None:
        #             distance = await self._haversine(center_lat, center_lon, prop.latitude, prop.longitude)
        #             if distance <= radius_km:
        #                 filtered_by_radius.append(prop)
        #     properties_orm = filtered_by_radius
            # Note: If radius filter is applied AFTER pagination, total_count might be misleading
            # for the final set. For accurate total_count with radius, radius filter must be in DB query.
            # For now, total_count is based on pre-radius, pre-pagination filters.

        logger.info(f"Search returned {len(properties_orm)} properties for page {filters.page} (total matching structured filters: {total_count}).")
        return properties_orm, total_count


    async def get_property_by_id(self, property_id: uuid.UUID) -> Optional[PropertyModel]:
        """
        Retrieves a single property by its ID, with owner and images.
        """
        logger.debug(f"Fetching property by ID: {property_id}")
        stmt = (
            select(PropertyModel)
            .where(PropertyModel.id == property_id)
            .options(
                selectinload(PropertyModel.owner), 
                selectinload(PropertyModel.images),
                selectinload(PropertyModel.embedding) # If you want to show embedding details
            )
        )
        result = await self.db_session.execute(stmt)
        property_orm = result.scalar_one_or_none()
        if property_orm:
            logger.info(f"Property found: {property_orm.title}")
        else:
            logger.warning(f"Property with ID {property_id} not found.")
        return property_orm

    # Placeholder for create_property, update_property, delete_property
    # async def create_property(self, property_in: PropertyCreate, owner_id: uuid.UUID) -> PropertyModel: ...
    # async def update_property(self, property_id: uuid.UUID, property_in: PropertyUpdate, owner_id: uuid.UUID) -> Optional[PropertyModel]: ...
    # async def delete_property(self, property_id: uuid.UUID, owner_id: uuid.UUID) -> bool: ...