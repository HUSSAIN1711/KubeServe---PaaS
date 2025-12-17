"""
User repository for database operations.
Handles all database queries related to users.
"""

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.schemas.user import UserCreate


class UserRepository:
    """Repository for user data access operations."""

    def __init__(self, db: AsyncSession):
        """
        Initialize user repository.

        Args:
            db: Database session
        """
        self.db = db

    async def get_by_id(self, user_id: int) -> Optional[User]:
        """
        Get a user by ID.

        Args:
            user_id: The user ID

        Returns:
            User object if found, None otherwise
        """
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        """
        Get a user by email.

        Args:
            email: The user email

        Returns:
            User object if found, None otherwise
        """
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def create(self, user_data: UserCreate, password_hash: str) -> User:
        """
        Create a new user.

        Args:
            user_data: User creation data
            password_hash: Hashed password

        Returns:
            Created User object
        """
        user = User(
            email=user_data.email,
            password_hash=password_hash,
            role=user_data.role,
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def update(self, user: User) -> User:
        """
        Update an existing user.

        Args:
            user: User object to update

        Returns:
            Updated User object
        """
        await self.db.commit()
        await self.db.refresh(user)
        return user

