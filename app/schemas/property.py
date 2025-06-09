# File: agentic_rental_platform/app/schemas/property.py
import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from pydantic import BaseModel, Field, HttpUrl # Removed field_validator as not used in this version

# --- Property Image Schemas ---
class PropertyImageBase(BaseModel):
    image_url: HttpUrl = Field(..., example="https://example.com/image.jpg")
    caption: Optional[str] = Field(None, example="Living room view")
    is_primary: bool = Field(default=False)
    order_index: int = Field(default=0)

class PropertyImageCreate(PropertyImageBase):
    pass

class PropertyImageUpdate(BaseModel):
    image_url: Optional[HttpUrl] = None
    caption: Optional[str] = None
    is_primary: Optional[bool] = None
    order_index: Optional[int] = None

class PropertyImage(PropertyImageBase): # For API responses
    id: uuid.UUID

    class Config:
        from_attributes = True


# --- Property Embedding Schema (Minimal, mostly for internal use or admin) ---
class PropertyEmbeddingBase(BaseModel):
    source_text_hash: Optional[str] = None

class PropertyEmbedding(PropertyEmbeddingBase): # For API responses
    id: uuid.UUID
    property_id: uuid.UUID
    # embedding: List[float] # Usually not exposed
    # updated_at: datetime 

    class Config:
        from_attributes = True


# --- Main Property Schemas ---
class PropertyBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=255, example="Spacious 2BR Apartment Downtown")
    description: str = Field(..., min_length=10, example="A beautiful and bright apartment with city views.")
    address_line1: str = Field(..., example="123 Main St")
    address_line2: Optional[str] = Field(None, example="Apt 4B")
    city: str = Field(..., example="San Francisco")
    state_province: str = Field(..., example="CA")
    postal_code: str = Field(..., example="94107")
    country: str = Field(default="US", example="US")
    
    latitude: Optional[float] = Field(None, ge=-90, le=90, example=37.7749)
    longitude: Optional[float] = Field(None, ge=-180, le=180, example=-122.4194)
    
    property_type: str = Field(..., example="apartment") 
    num_bedrooms: int = Field(..., ge=0, example=2)
    num_bathrooms: float = Field(..., ge=0, example=1.5)

    area_sqft: Optional[int] = Field(None, gt=0, example=1000)
    
    rent_price: float = Field(..., gt=0, example=3500.00)
    rent_price_currency: str = Field(default="USD", example="USD")
    rent_price_period: str = Field(default="monthly", example="monthly")

    status: str = Field(default="available", example="available")
    availability_date: Optional[date] = Field(None, example="2024-08-01")
    
    amenities: Optional[Dict[str, Any]] = Field(None, example={"parking": True, "gym": False, "pool": True})
    rules: Optional[str] = Field(None, example="No pets allowed. No smoking.")
    is_published: bool = Field(default=False) # Default to not published


class PropertyCreate(PropertyBase):
    # owner_id will be derived from the authenticated user in the service layer
    images: Optional[List[PropertyImageCreate]] = Field(default_factory=list)


class PropertyUpdate(BaseModel): 
    title: Optional[str] = Field(None, min_length=3, max_length=255)
    description: Optional[str] = Field(None, min_length=10)
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state_province: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    property_type: Optional[str] = None
    num_bedrooms: Optional[int] = Field(None, ge=0)
    num_bathrooms: Optional[float] = Field(None, ge=0)
    area_sqft: Optional[int] = Field(None, gt=0)
    rent_price: Optional[float] = Field(None, gt=0)
    rent_price_currency: Optional[str] = None
    rent_price_period: Optional[str] = None
    status: Optional[str] = None
    availability_date: Optional[date] = None
    amenities: Optional[Dict[str, Any]] = None
    rules: Optional[str] = None
    is_published: Optional[bool] = None


class Property(PropertyBase): # For API responses
    id: uuid.UUID
    owner_id: uuid.UUID # Good to show owner_id
    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime] = None
    view_count: int = Field(default=0)

    images: List[PropertyImage] = Field(default_factory=list)
    # embedding: Optional[PropertyEmbedding] # Usually not shown directly in list/detail views

    class Config:
        from_attributes = True

class PropertyList(BaseModel): # For paginated property lists
    items: List[Property]
    total: int
    page: int
    size: int
    # pages: Optional[int] = None # Can be calculated on frontend: math.ceil(total / size)