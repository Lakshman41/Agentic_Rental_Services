# File: agentic_rental_platform/app/models/property_embedding.py
import uuid
from typing import Optional, TYPE_CHECKING, Any, List as PyList # Renamed to PyList to avoid conflict with Mapped[List]
from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import UserDefinedType
from app.models.base import TimestampedModel

if TYPE_CHECKING:
    from .property import Property

class Vector(UserDefinedType):
    cache_ok = True
    def get_col_spec(self, **kw: Any) -> str:
        return "vector(384)"

class PropertyEmbedding(TimestampedModel):
    __tablename__ = "property_embeddings"
    property_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("properties.id", ondelete="CASCADE"), unique=True, index=True, nullable=False
    )
    embedding: Mapped[PyList[float]] = mapped_column(Vector, nullable=False)
    source_text_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    
    property: Mapped["Property"] = relationship(back_populates="embedding", lazy="selectin")
    def __repr__(self) -> str:
        return f"<PropertyEmbedding(id={self.id}, property_id={self.property_id})>"