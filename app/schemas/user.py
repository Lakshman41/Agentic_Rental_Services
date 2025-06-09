# File: app/schemas/user.py
from typing import Optional
from pydantic import BaseModel, EmailStr, Field
import uuid
from datetime import datetime # For created_at, updated_at in User response

class UserBase(BaseModel):
    email: EmailStr = Field(..., example="user@example.com")
    full_name: Optional[str] = Field(None, example="John Doe")
    is_active: bool = True # Default to True

class UserCreate(UserBase):
    password: str = Field(..., min_length=8, example="SecurePassword123")

class UserUpdate(BaseModel): # Allow partial updates
    email: Optional[EmailStr] = Field(None, example="user_new@example.com")
    full_name: Optional[str] = Field(None, example="Johnathan Doe")
    password: Optional[str] = Field(None, min_length=8, example="NewSecurePassword123")
    is_active: Optional[bool] = None
    role: Optional[str] = Field(None, example="agent") # Allow role update by admin

class UserInDBBase(UserBase):
    id: uuid.UUID
    hashed_password: str # This will be present in the ORM model
    role: str = Field("client", example="client")
    created_at: datetime
    updated_at: datetime
    email_verified_at: Optional[datetime] = None
    last_login_at: Optional[datetime] = None
    preferences: Optional[dict] = None
    profile_picture_url: Optional[str] = None
    
    class Config:
        from_attributes = True

class User(UserInDBBase): # Schema for API responses
    # Exclude sensitive fields for responses
    hashed_password: Optional[str] = Field(None, exclude=True)

class UserInDB(UserInDBBase): # Represents the full user object as in DB (for service layer)
    pass 