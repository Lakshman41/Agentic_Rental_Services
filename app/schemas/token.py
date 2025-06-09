# File: app/schemas/token.py
from typing import Optional
from pydantic import BaseModel

class Token(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"

class TokenPayload(BaseModel): # Data encoded in the JWT
    sub: Optional[str] = None # Subject (usually user_id)
    type: Optional[str] = None # "access" or "refresh"

class RefreshTokenRequest(BaseModel): # For the refresh token endpoint
    refresh_token: str