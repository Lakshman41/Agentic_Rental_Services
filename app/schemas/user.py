# File: app/schemas/user.py
from typing import Optional
from pydantic import BaseModel, EmailStr, Field
import uuid
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr = Field(..., example="user@example.com")
    full_name: Optional[str] = Field(None, example="John Doe")
    is_active: bool = True

class UserCreate(UserBase):
    password: str = Field(..., min_length=8, example="SecurePassword123")

class UserUpdate(BaseModel): # For potential future use
    email: Optional[EmailStr] = Field(None, example="user_new@example.com")
    full_name: Optional[str] = Field(None, example="Johnathan Doe")
    password: Optional[str] = Field(None, min_length=8, example="NewSecurePassword123")
    is_active: Optional[bool] = None
    role: Optional[str] = Field(None, example="agent")

class UserInDBBase(UserBase): # Base for DB representation and API response
    id: uuid.UUID
    role: str = Field("client", example="client") # Default role
    created_at: datetime
    updated_at: datetime
    # Add other fields from your ORM model that you want in responses (except password)
    email_verified_at: Optional[datetime] = None
    last_login_at: Optional[datetime] = None
    # preferences: Optional[dict] = None # If you want to expose this
    # profile_picture_url: Optional[str] = None

    class Config:
        from_attributes = True

class User(UserInDBBase): # Schema for API responses (what clients see)
    pass # Inherits all from UserInDBBase, hashed_password is NOT here

class UserInDB(UserInDBBase): # Represents full user object in DB (for service layer)
    hashed_password: str # Only for internal use / DB model mapping