# File: agentic_rental_platform/app/models/property.py
import uuid
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime, date
from sqlalchemy import String, Text, Boolean, Integer, SmallInteger, Date, func, ForeignKey, DECIMAL, DateTime # Added DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import TimestampedModel

if TYPE_CHECKING:
    from .user import User
    from .property_image import PropertyImage
    from .property_embedding import PropertyEmbedding

class Property(TimestampedModel):
    __tablename__ = "properties"
    owner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    address_line1: Mapped[str] = mapped_column(String(255), nullable=False)
    address_line2: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    city: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    state_province: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    postal_code: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    country: Mapped[str] = mapped_column(String(50), default="US", nullable=False)
    latitude: Mapped[Optional[float]] = mapped_column(DECIMAL(9,6), nullable=True, index=True)
    longitude: Mapped[Optional[float]] = mapped_column(DECIMAL(9,6), nullable=True, index=True)
    property_type: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    num_bedrooms: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    num_bathrooms: Mapped[float] = mapped_column(DECIMAL(3,1), default=0.0, nullable=False)
    area_sqft: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    rent_price: Mapped[float] = mapped_column(DECIMAL(10,2), nullable=False)
    rent_price_currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    rent_price_period: Mapped[str] = mapped_column(String(20), default="monthly", nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="available", index=True, nullable=False)
    availability_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    amenities: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    rules: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True) # Corrected
    view_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    archived_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    owner: Mapped["User"] = relationship(back_populates="properties_owned", lazy="selectin")
    images: Mapped[List["PropertyImage"]] = relationship(
        "PropertyImage", back_populates="property", cascade="all, delete-orphan", lazy="selectin"
    )
    embedding: Mapped[Optional["PropertyEmbedding"]] = relationship(
        "PropertyEmbedding", back_populates="property", uselist=False, cascade="all, delete-orphan", lazy="selectin"
    )
    def __repr__(self) -> str:
        return f"<Property(id={self.id}, title='{self.title[:30]}...', owner_id={self.owner_id})>"