# File: agentic_rental_platform/app/services/user_service.py
from typing import Optional, List
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import get_password_hash
from app.schemas.user import UserCreate
from app.models.user import User as UserModel
from app.core.logging import logger

class UserService:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def get_user_by_id(self, user_id: uuid.UUID) -> Optional[UserModel]:
        logger.debug(f"DB: Attempting to get user by ID: {user_id}")
        statement = select(UserModel).where(UserModel.id == user_id)
        result = await self.db_session.execute(statement)
        user = result.scalar_one_or_none()
        if user: logger.info(f"DB: User found by ID: {user_id} - {user.email}")
        else: logger.warning(f"DB: User not found by ID: {user_id}")
        return user

    async def get_user_by_email(self, email: str) -> Optional[UserModel]:
        logger.debug(f"DB: Attempting to get user by email: {email}")
        statement = select(UserModel).where(UserModel.email == email.lower())
        result = await self.db_session.execute(statement)
        user = result.scalar_one_or_none()
        if user: logger.info(f"DB: User found by email: {email}")
        else: logger.warning(f"DB: User not found by email: {email}")
        return user

    async def create_user(self, user_in: UserCreate) -> UserModel:
        logger.info(f"DB: Attempting to create user with email: {user_in.email}")
        existing_user = await self.get_user_by_email(user_in.email)
        if existing_user:
            logger.warning(f"DB: User creation failed: Email {user_in.email} already registered.")
            raise ValueError(f"A user with email {user_in.email} already exists.")
        hashed_password = get_password_hash(user_in.password)
        db_user = UserModel(
            email=user_in.email.lower(),
            hashed_password=hashed_password,
            full_name=user_in.full_name,
            is_active=user_in.is_active if user_in.is_active is not None else True,
            role="client" 
        )
        self.db_session.add(db_user)
        await self.db_session.commit()
        await self.db_session.refresh(db_user)
        logger.info(f"DB: User created successfully: ID {db_user.id}, Email {db_user.email}")
        return db_user

    async def get_users(self, skip: int = 0, limit: int = 100) -> List[UserModel]:
        logger.debug(f"DB: Fetching users with skip: {skip}, limit: {limit}")
        statement = select(UserModel).offset(skip).limit(limit).order_by(UserModel.created_at)
        result = await self.db_session.execute(statement)
        users = result.scalars().all()
        return list(users)

    async def update_user_role(self, user_id: uuid.UUID, new_role: str) -> Optional[UserModel]:
        logger.info(f"DB: Attempting to update role for user ID {user_id} to {new_role}")
        user = await self.get_user_by_id(user_id)
        if not user: return None
        user.role = new_role
        self.db_session.add(user)
        await self.db_session.commit()
        await self.db_session.refresh(user)
        logger.info(f"DB: User ID {user_id} role updated to {new_role}")
        return user

    async def deactivate_user(self, user_id: uuid.UUID) -> Optional[UserModel]:
        logger.info(f"DB: Attempting to deactivate user ID {user_id}")
        user = await self.get_user_by_id(user_id)
        if not user: return None
        user.is_active = False
        self.db_session.add(user)
        await self.db_session.commit()
        await self.db_session.refresh(user)
        logger.info(f"DB: User ID {user_id} deactivated.")
        return user