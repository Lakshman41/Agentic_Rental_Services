# File: app/schemas/__init__.py
from .token import Token, TokenPayload, RefreshTokenRequest
from .user import User, UserCreate, UserUpdate, UserInDB # UserInDB might be more for service layer
from .property import (
    Property, PropertyCreate, PropertyUpdate, PropertyList,
    PropertyImage, PropertyImageCreate, PropertyImageUpdate,
    PropertyEmbedding
)
from .search import (
    PropertySearchFilters, LocationFilter,
    SavedSearch, SavedSearchCreate, SavedSearchUpdate
)

# You can define __all__ if you want to control 'from app.schemas import *' behavior
# Example:
# __all__ = [
#     "Token", "TokenPayload", "RefreshTokenRequest",
#     "User", "UserCreate", "UserUpdate",
#     "Property", "PropertyCreate", "PropertyUpdate", "PropertyList",
#     "PropertyImage", "PropertyImageCreate", "PropertyImageUpdate",
#     "PropertyEmbedding",
#     "PropertySearchFilters", "LocationFilter",
#     "SavedSearch", "SavedSearchCreate", "SavedSearchUpdate",
# ]