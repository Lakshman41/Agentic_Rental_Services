# File: agentic_rental_platform/app/services/property_service.py
from typing import List, Optional, Dict, Any, Tuple
import uuid
import math 

from sqlalchemy import select, func, text, literal_column, or_ # Added or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.logging import logger
from app.models.property import Property as PropertyModel
from app.models.property_embedding import PropertyEmbedding as PropertyEmbeddingModel # For semantic search later
from app.schemas.search import PropertySearchFilters
# from sentence_transformers import SentenceTransformer # For semantic search later

# --- SentenceTransformer Model Loading ---
# This should ideally be handled more gracefully, e.g., in app startup or a dedicated ML model service
# For simplicity now, we load it here. BE AWARE: This adds startup time and memory use.
# Consider making EMBEDDING_MODEL_NAME configurable via settings.
EMBEDDING_MODEL_NAME = 'all-MiniLM-L6-v2' # ~120MB model, good balance
# EMBEDDING_MODEL_NAME = 'paraphrase-MiniLM-L6-v2' # Another option
# EMBEDDING_MODEL_NAME = 'multi-qa-MiniLM-L6-cos-v1' # Good for QA/search

try:
    from sentence_transformers import SentenceTransformer
    embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    logger.info(f"SentenceTransformer model '{EMBEDDING_MODEL_NAME}' loaded successfully for PropertyService.")
except ImportError:
    logger.error("sentence-transformers library not found. Semantic search will be disabled. "
                 "Please install it: pip install sentence-transformers")
    embedding_model = None
except Exception as e:
    logger.error(f"Failed to load SentenceTransformer model '{EMBEDDING_MODEL_NAME}': {e}. Semantic search may be impaired.")
    embedding_model = None
# --- End Model Loading ---


EARTH_RADIUS_KM = 6371.0

class PropertyService:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
        # self.embedding_model = None # Initialize later for semantic search
        # The model is loaded globally for now.
        # In a larger app, you might inject this or use a shared instance.
        self.embedding_model = embedding_model 

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
    ) -> Tuple[List[PropertyModel], int]: # Returns list of ORM models and total count
        logger.info(f"Property search with filters: {filters.model_dump(exclude_none=True)}")

        semantic_property_ids_with_distance: Optional[List[Dict[str, Any]]] = None

        # --- 1. Semantic Search (if query is provided and model is available) ---
        if filters.query and self.embedding_model:
            try:
                logger.debug(f"Performing semantic search for query: '{filters.query}'")
                query_embedding_list = self.embedding_model.encode(filters.query).tolist()
                
                # pgvector expects vector as a string like '[1.0,2.1,3.3]'
                query_embedding_str = str(query_embedding_list).replace(" ", "") # Ensure no spaces for some DBs

                # We indexed with vector_cosine_ops, so use <=> (cosine distance)
                # Smaller distance means more similar (cosine distance = 1 - cosine_similarity)
                # Limit initial semantic results. This limit helps manage performance before further filtering.
                # A common strategy is to fetch more than needed (e.g., 5x page size or a fixed cap like 100-200)
                # and then apply structured filters and pagination.
                SEMANTIC_SEARCH_CANDIDATE_LIMIT = 200 # Fetch top N candidates via semantic search
                
                # Use text() for the vector operation part to ensure correct SQL syntax
                # The label 'distance' is important for ORDER BY
                # The vector string needs to be quoted within the SQL if it's directly embedded.
                # Using bind parameters is safer if the SQL construction allows it for this.
                # For direct embedding of the vector string:
                distance_calculation = f"embedding <=> '{query_embedding_str}'"
                
                stmt = (
                    select(
                        PropertyEmbeddingModel.property_id, 
                        literal_column(distance_calculation).label("distance")
                    )
                    .order_by(literal_column("distance").asc()) # Order by cosine distance (smaller is better)
                    .limit(SEMANTIC_SEARCH_CANDIDATE_LIMIT)
                )
                
                logger.debug(f"Executing semantic search SQL (parameters hidden for brevity if any)")
                result = await self.db_session.execute(stmt)
                # Get results as a list of dictionaries (property_id, distance)
                semantic_property_ids_with_distance = [
                    {"property_id": row.property_id, "distance": row.distance} 
                    for row in result.mappings().all() # Use mappings() for dict-like rows
                ]

                if not semantic_property_ids_with_distance:
                    logger.info("Semantic search yielded no results. Returning empty list.")
                    return [], 0 
                logger.info(f"Semantic search found {len(semantic_property_ids_with_distance)} potential property candidates.")
            except Exception as e:
                logger.error(f"Error during semantic search: {e}", exc_info=True)
                # Fallback: If semantic search fails, proceed without semantic filtering
                semantic_property_ids_with_distance = None 
        else:
            if filters.query and not self.embedding_model:
                logger.warning("Semantic search query provided, but embedding model is not available.")
            # else: (no query provided)
            # logger.debug("No query provided for semantic search.")
        # --- End Semantic Search ---


        # --- 2. Build Base Query for Properties ---
        query = select(PropertyModel).options(
            selectinload(PropertyModel.owner),
            selectinload(PropertyModel.images)
        )

        # --- Apply Semantic Search Results (if any) ---
        # If semantic search ran, filter by the property IDs it found.
        if semantic_property_ids_with_distance is not None:
            if not semantic_property_ids_with_distance: # Semantic search ran but found nothing
                return [], 0 # Short-circuit if semantic search is primary and yields nothing
            
            # Extract just the IDs for the IN clause
            property_ids_from_semantic = [item["property_id"] for item in semantic_property_ids_with_distance]
            query = query.where(PropertyModel.id.in_(property_ids_from_semantic))
            # We might want to preserve the semantic search order later, this requires more complex SQL.
            # For now, structured filters and sorting will re-order.

        # --- Apply Structured Filters (as before) ---
        if filters.city: query = query.where(PropertyModel.city.ilike(f"%{filters.city}%"))
        # ... (all other structured filters: state, postal, type, bedrooms, bathrooms, price, availability etc.) ...
        if filters.state_province: query = query.where(PropertyModel.state_province.ilike(f"%{filters.state_province}%"))
        if filters.postal_code: query = query.where(PropertyModel.postal_code == filters.postal_code)
        if filters.property_type: query = query.where(PropertyModel.property_type.ilike(f"%{filters.property_type}%"))
        if filters.min_bedrooms is not None: query = query.where(PropertyModel.num_bedrooms >= filters.min_bedrooms)
        if filters.max_bedrooms is not None: query = query.where(PropertyModel.num_bedrooms <= filters.max_bedrooms)
        if filters.min_bathrooms is not None: query = query.where(PropertyModel.num_bathrooms >= filters.min_bathrooms)
        if filters.max_bathrooms is not None: query = query.where(PropertyModel.num_bathrooms <= filters.max_bathrooms)
        if filters.min_area_sqft is not None: query = query.where(PropertyModel.area_sqft >= filters.min_area_sqft)
        if filters.max_area_sqft is not None: query = query.where(PropertyModel.area_sqft <= filters.max_area_sqft)
        if filters.min_rent_price is not None: query = query.where(PropertyModel.rent_price >= filters.min_rent_price)
        if filters.max_rent_price is not None: query = query.where(PropertyModel.rent_price <= filters.max_rent_price)
        if filters.rent_price_period: query = query.where(PropertyModel.rent_price_period.ilike(f"%{filters.rent_price_period}%"))
        if filters.available_from: query = query.where(or_(PropertyModel.availability_date == None, PropertyModel.availability_date >= filters.available_from))
        
        query = query.where(PropertyModel.is_published == True)
        query = query.where(PropertyModel.archived_at == None)


        # --- 3. Count Total Matching Properties (after all DB filters) ---
        count_subquery = query.order_by(None).alias("count_subquery")
        count_query = select(func.count()).select_from(count_subquery)
        total_count_result = await self.db_session.execute(count_query)
        total_count = total_count_result.scalar_one()
        
        if total_count == 0:
            logger.info("No properties found matching all combined filters.")
            return [], 0

        # --- 4. Apply Sorting ---
        # If semantic search was performed, 'relevance' (distance) is a primary sort.
        # Otherwise, use specified or default sort.
        if filters.sort_by == "relevance" and semantic_property_ids_with_distance is not None:
            # This is more complex. We need to join with embeddings or use a CASE statement
            # to order by the pre-calculated distances.
            # For now, we'll just log it and use default sort if 'relevance' is chosen without semantic results.
            # A proper implementation would involve joining or CTEs to use the 'distance'.
            logger.info("Relevance sort requested with semantic results. Implementing precise relevance sort is complex and will be refined.")
            # Fallback to default sort for now if 'relevance' is chosen
            query = query.order_by(PropertyModel.created_at.desc()) 
        elif filters.sort_by:
            if filters.sort_by == "rent_price_asc": query = query.order_by(PropertyModel.rent_price.asc())
            elif filters.sort_by == "rent_price_desc": query = query.order_by(PropertyModel.rent_price.desc())
            elif filters.sort_by == "date_posted_desc": query = query.order_by(PropertyModel.created_at.desc())
            else: query = query.order_by(PropertyModel.created_at.desc()) # Default if sort_by is unknown
        else:
            # Default sort if nothing specified and not semantic 'relevance'
            query = query.order_by(PropertyModel.created_at.desc())
            
        # --- 5. Apply Pagination ---
        query = query.offset((filters.page - 1) * filters.size).limit(filters.size)

        results = await self.db_session.execute(query)
        properties_orm: List[PropertyModel] = list(results.scalars().unique().all())

        # --- 6. Location Radius Filter (Post-DB Haversine - applied after pagination) ---
        final_properties_list = properties_orm
        # ... (Haversine logic as before) ...
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
        
        logger.info(f"Search returned {len(final_properties_list)} properties for page {filters.page} (total matching all DB filters: {total_count}).")
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

    from app.schemas.property import PropertyCreate # Ensure this is imported for create_property_basic
    async def create_property_basic(self, property_in: PropertyCreate, owner_id: uuid.UUID) -> PropertyModel:
        logger.info(f"User {owner_id} creating basic property: {property_in.title}")
        db_property = PropertyModel(
            **property_in.model_dump(exclude={"images"}), 
            owner_id=owner_id,
            is_published=True 
        )
        self.db_session.add(db_property)
        await self.db_session.commit()
        await self.db_session.refresh(db_property)
        logger.info(f"Property '{db_property.title}' created with ID {db_property.id}")
        return db_property

    # TODO: Implement create_property, update_property, delete_property
    # async def create_property(self, property_in: PropertyCreate, owner_id: uuid.UUID) -> PropertyModel: ...