# File: agentic_rental_platform/app/schemas/search.py
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator, conint, confloat
import uuid
from datetime import date, datetime # Added datetime for SavedSearch

# --- Search Filter Schemas ---
class LocationFilter(BaseModel):
    latitude: confloat(ge=-90, le=90) = Field(..., example=37.7749)
    longitude: confloat(ge=-180, le=180) = Field(..., example=-122.4194)
    radius_km: confloat(gt=0, le=200) = Field(default=5.0, example=5.0)

class PropertySearchFilters(BaseModel):
    query: Optional[str] = Field(None, description="Keywords or natural language query for semantic search", example="apartment near park with good sunlight")
    
    city: Optional[str] = Field(None, example="San Francisco")
    state_province: Optional[str] = Field(None, example="CA")
    postal_code: Optional[str] = Field(None, example="94107")
    location: Optional[LocationFilter] = Field(None, description="Geo-coordinates and radius for location-based search")

    property_type: Optional[str] = Field(None, example="apartment")
    min_bedrooms: Optional[conint(ge=0)] = Field(None, example=2)
    max_bedrooms: Optional[conint(ge=0)] = Field(None, example=3)
    min_bathrooms: Optional[confloat(ge=0)] = Field(None, example=1.5)
    max_bathrooms: Optional[confloat(ge=0)] = Field(None, example=2.0)
    min_area_sqft: Optional[conint(gt=0)] = Field(None, example=800)
    max_area_sqft: Optional[conint(gt=0)] = Field(None, example=1200)
    
    min_rent_price: Optional[confloat(ge=0)] = Field(None, example=2500.00)
    max_rent_price: Optional[confloat(ge=0)] = Field(None, example=4000.00)
    rent_price_period: Optional[str] = Field(None, example="monthly")

    available_from: Optional[date] = Field(None, example="2024-08-01")
    available_until: Optional[date] = Field(None, example="2024-09-01")

    required_amenities: Optional[List[str]] = Field(None, example=["parking", "laundry_in_unit"])
    
    sort_by: Optional[str] = Field(None, description="e.g., 'rent_price_asc', 'rent_price_desc', 'date_posted_desc', 'relevance'", example="rent_price_asc")
    
    page: conint(ge=1) = Field(default=1)
    size: conint(ge=1, le=100) = Field(default=10)

    @field_validator('max_bedrooms')
    def max_bedrooms_gte_min(cls, v, info): # Changed values to info for Pydantic v2
        # Pydantic v2: info.data contains the input data for the model
        min_val = info.data.get('min_bedrooms')
        if min_val is not None and v is not None and v < min_val:
            raise ValueError('max_bedrooms must be greater than or equal to min_bedrooms')
        return v

    @field_validator('max_bathrooms')
    def max_bathrooms_gte_min(cls, v, info): # Changed values to info
        min_val = info.data.get('min_bathrooms')
        if min_val is not None and v is not None and v < min_val:
            raise ValueError('max_bathrooms must be greater than or equal to min_bathrooms')
        return v
    
    @field_validator('max_area_sqft')
    def max_area_sqft_gte_min(cls, v, info):
        min_val = info.data.get('min_area_sqft')
        if min_val is not None and v is not None and v < min_val:
            raise ValueError('max_area_sqft must be greater than or equal to min_area_sqft')
        return v

    @field_validator('max_rent_price')
    def max_rent_price_gte_min(cls, v, info):
        min_val = info.data.get('min_rent_price')
        if min_val is not None and v is not None and v < min_val:
            raise ValueError('max_rent_price must be greater than or equal to min_rent_price')
        return v


# --- Saved Search Schemas ---
class SavedSearchBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, example="My SF 2BR Apartment Hunt")
    # When creating, search_criteria will be a PropertySearchFilters object
    # When reading from DB (where it's JSONB), it will be parsed back if possible,
    # or can be represented as Dict[str, Any] if not strictly typed on read for flexibility.
    search_criteria: PropertySearchFilters 

class SavedSearchCreate(SavedSearchBase):
    pass

class SavedSearchUpdate(BaseModel): # All fields optional for update
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    search_criteria: Optional[PropertySearchFilters] = None

class SavedSearch(SavedSearchBase): # For API responses
    id: uuid.UUID
    user_id: uuid.UUID # Usually good to show who owns it, but depends on API design
    created_at: datetime
    # updated_at: datetime # Can be added from ORM model

    class Config:
        from_attributes = True