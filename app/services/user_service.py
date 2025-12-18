"""
User service containing business logic for user operations.
"""

import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserResponse
from app.core.security import verify_password, get_password_hash, create_access_token

logger = logging.getLogger(__name__)


class UserService:
    """Service for user business logic operations."""

    def __init__(self, db: AsyncSession):
        """
        Initialize user service.

        Args:
            db: Database session
        """
        self.repository = UserRepository(db)

    async def create_user(self, user_data: UserCreate) -> UserResponse:
        """
        Create a new user with business logic validation.
        Also creates an isolated Kubernetes namespace for the user.

        Args:
            user_data: User creation data

        Returns:
            Created user response

        Raises:
            HTTPException: If email already exists or validation fails
        """
        # Business rule: Check if email already exists
        existing_user = await self.repository.get_by_email(user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        # Business rule: Hash password before storing
        password_hash = get_password_hash(user_data.password)

        # Create user via repository
        user = await self.repository.create(user_data, password_hash)
        
        # Create isolated Kubernetes namespace for the user
        # This is done after user creation so we have the user ID
        try:
            from app.core.kubernetes_client import KubernetesClient
            k8s_client = KubernetesClient()
            namespace = k8s_client.setup_user_namespace(user.id)
            logger.info(f"Created Kubernetes namespace {namespace} for user {user.id}")
        except Exception as e:
            # Log error but don't fail user creation
            # This allows the system to work even if Kubernetes is not available
            logger.warning(
                f"Failed to create Kubernetes namespace for user {user.id}: {str(e)}. "
                "User was created but namespace setup failed. This may need manual intervention."
            )
        
        return UserResponse.model_validate(user)

    async def authenticate_user(self, email: str, password: str) -> Optional[UserResponse]:
        """
        Authenticate a user and return user data if credentials are valid.

        Args:
            email: User email
            password: User password

        Returns:
            UserResponse if authentication successful, None otherwise
        """
        user = await self.repository.get_by_email(email)
        if not user:
            return None

        if not verify_password(password, user.password_hash):
            return None

        return UserResponse.model_validate(user)

    async def get_user_by_id(self, user_id: int) -> Optional[UserResponse]:
        """
        Get a user by ID.

        Args:
            user_id: User ID

        Returns:
            UserResponse if found, None otherwise
        """
        user = await self.repository.get_by_id(user_id)
        if not user:
            return None
        return UserResponse.model_validate(user)

    async def get_user_by_email(self, email: str) -> Optional[UserResponse]:
        """
        Get a user by email.

        Args:
            email: User email

        Returns:
            UserResponse if found, None otherwise
        """
        user = await self.repository.get_by_email(email)
        if not user:
            return None
        return UserResponse.model_validate(user)

    def create_access_token_for_user(self, user: UserResponse) -> str:
        """
        Create an access token for a user.

        Args:
            user: User response object

        Returns:
            JWT access token string
        """
        token_data = {
            "sub": str(user.id),  # 'sub' is the standard JWT claim for subject
            "email": user.email,
        }
        return create_access_token(data=token_data)

