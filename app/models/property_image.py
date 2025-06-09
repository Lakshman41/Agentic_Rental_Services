# File: agentic_rental_platform/app/models/property_image.py
import uuid
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Boolean, SmallInteger, ForeignKey, DateTime, func # Added DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import TimestampedModel # Use TimestampedModel for created_at/updated_at

if TYPE_CHECKING:
    from .property import Property

class PropertyImage(TimestampedModel): # Inherit from TimestampedModel
    __tablename__ = "property_images"
    property_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("properties.id", ondelete="CASCADE"), index=True, nullable=False)
    image_url: Mapped[str] = mapped_column(String(512), nullable=False)
    caption: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    order_index: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    
    property: Mapped["Property"] = relationship(back_populates="images", lazy="selectin")
    def __repr__(self) -> str:
        return f"<PropertyImage(id={self.id}, property_id={self.property_id}, url='{self.image_url[:30]}...')>"