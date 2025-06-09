# File: agentic_rental_platform/app/models/user.py
import uuid
from typing import Optional, List, TYPE_CHECKING # Added List
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, func, JSON # Added JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import TimestampedModel

if TYPE_CHECKING:
    from .property import Property # For properties_owned relationship
    from .saved_search import SavedSearch

class User(TimestampedModel):
    __tablename__ = "users"
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone_number: Mapped[Optional[str]] = mapped_column(String(30), unique=True, nullable=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    role: Mapped[str] = mapped_column(String(50), default="client", nullable=False, index=True)
    email_verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    preferences: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    profile_picture_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    
    properties_owned: Mapped[List["Property"]] = relationship(
        "Property", back_populates="owner", cascade="all, delete-orphan", lazy="selectin"
    )
    saved_searches: Mapped[List["SavedSearch"]] = relationship( # <--- ADD THIS RELATIONSHIP
        "SavedSearch", back_populates="user", cascade="all, delete-orphan", lazy="selectin"
    )
    # Add other relationships (bookings, conversations) later

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}', role='{self.role}')>"