import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import declared_attr, Mapped, mapped_column
from app.core.database import Base

class BaseModel(Base):
    __abstract__ = True
    @declared_attr
    def __tablename__(cls) -> str:
        import re
        name_parts = re.sub(r'(?<!^)(?=[A-Z])', '_', cls.__name__).lower()
        return f"{name_parts}s"
    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )

class TimestampedModel(BaseModel):
    __abstract__ = True
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )