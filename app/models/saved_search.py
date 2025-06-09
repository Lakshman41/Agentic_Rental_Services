# File: agentic_rental_platform/app/models/saved_search.py
import uuid
from typing import TYPE_CHECKING, Dict, Any # For type hinting JSONB content
from datetime import datetime

from sqlalchemy import String, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import TimestampedModel # Inherits id, created_at, updated_at

if TYPE_CHECKING:
    from .user import User # noqa

class SavedSearch(TimestampedModel):
    """
    SavedSearch ORM Model.
    Stores user-saved search criteria.
    Table name will be 'saved_searches'.
    """
    __tablename__ = "saved_searches" # Explicitly set for clarity

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False, comment="User-defined name for the saved search")
    
    # Store the search criteria as a JSON object.
    # This will typically be the PropertySearchFilters Pydantic model serialized to dict.
    search_criteria: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False, comment="JSON object of search filters")

    # --- Relationships ---
    user: Mapped["User"] = relationship(back_populates="saved_searches", lazy="selectin")

    def __repr__(self) -> str:
        return f"<SavedSearch(id={self.id}, name='{self.name}', user_id={self.user_id})>"