"""
Model service containing business logic for model operations.
"""

from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.repositories.model_repository import (
    ModelRepository,
    ModelVersionRepository,
    DeploymentRepository,
)
from app.schemas.model import (
    ModelCreate,
    ModelResponse,
    ModelVersionCreate,
    ModelVersionResponse,
    DeploymentCreate,
    DeploymentResponse,
)
from app.models.model import ModelVersionStatus


class ModelService:
    """Service for model business logic operations."""

    def __init__(self, db: AsyncSession):
        """
        Initialize model service.

        Args:
            db: Database session
        """
        self.repository = ModelRepository(db)
        self.version_repository = ModelVersionRepository(db)
        self.deployment_repository = DeploymentRepository(db)

    async def create_model(self, model_data: ModelCreate, user_id: int) -> ModelResponse:
        """
        Create a new model with business logic validation.

        Args:
            model_data: Model creation data
            user_id: The user ID creating the model

        Returns:
            Created model response

        Raises:
            HTTPException: If validation fails
        """
        # Business rule: Model names should be unique per user (optional check)
        # For now, we allow multiple models with same name for same user

        # Create model via repository
        model = await self.repository.create(model_data, user_id)
        return ModelResponse.model_validate(model)

    async def get_model(self, model_id: int, user_id: int) -> ModelResponse:
        """
        Get a model by ID, ensuring ownership.

        Args:
            model_id: Model ID
            user_id: User ID (for ownership verification)

        Returns:
            Model response

        Raises:
            HTTPException: If model not found or not owned by user
        """
        model = await self.repository.get_by_id(model_id, user_id)
        if not model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Model not found",
            )
        return ModelResponse.model_validate(model)

    async def get_all_models(self, user_id: int) -> List[ModelResponse]:
        """
        Get all models for a user.

        Args:
            user_id: User ID

        Returns:
            List of model responses
        """
        models = await self.repository.get_all_by_user(user_id)
        return [ModelResponse.model_validate(model) for model in models]

    async def delete_model(self, model_id: int, user_id: int) -> None:
        """
        Delete a model, ensuring ownership.

        Args:
            model_id: Model ID
            user_id: User ID (for ownership verification)

        Raises:
            HTTPException: If model not found or not owned by user
        """
        model = await self.repository.get_by_id(model_id, user_id)
        if not model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Model not found",
            )
        await self.repository.delete(model)


class ModelVersionService:
    """Service for model version business logic operations."""

    def __init__(self, db: AsyncSession):
        """
        Initialize model version service.

        Args:
            db: Database session
        """
        self.repository = ModelVersionRepository(db)
        self.model_repository = ModelRepository(db)

    async def create_version(
        self, version_data: ModelVersionCreate, user_id: int
    ) -> ModelVersionResponse:
        """
        Create a new model version with business logic validation.

        Args:
            version_data: Model version creation data
            user_id: User ID (for ownership verification)

        Returns:
            Created model version response

        Raises:
            HTTPException: If model not found or validation fails
        """
        # Business rule: Verify model exists and belongs to user
        model = await self.model_repository.get_by_id(version_data.model_id, user_id)
        if not model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Model not found",
            )

        # Business rule: Check if version tag already exists for this model
        existing_version = await self.repository.get_by_model_and_tag(
            version_data.model_id, version_data.version_tag
        )
        if existing_version:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Version tag '{version_data.version_tag}' already exists for this model",
            )

        # Create version via repository
        version = await self.repository.create(version_data)
        return ModelVersionResponse.model_validate(version)

    async def get_version(self, version_id: int, user_id: int) -> ModelVersionResponse:
        """
        Get a model version by ID, ensuring model ownership.

        Args:
            version_id: Version ID
            user_id: User ID (for ownership verification)

        Returns:
            Model version response

        Raises:
            HTTPException: If version not found or model not owned by user
        """
        version = await self.repository.get_by_id(version_id)
        if not version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Model version not found",
            )

        # Verify ownership through model
        model = await self.model_repository.get_by_id(version.model_id, user_id)
        if not model:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied",
            )

        return ModelVersionResponse.model_validate(version)

    async def get_versions_by_model(
        self, model_id: int, user_id: int
    ) -> List[ModelVersionResponse]:
        """
        Get all versions for a model, ensuring ownership.

        Args:
            model_id: Model ID
            user_id: User ID (for ownership verification)

        Returns:
            List of model version responses

        Raises:
            HTTPException: If model not found or not owned by user
        """
        # Verify ownership
        model = await self.model_repository.get_by_id(model_id, user_id)
        if not model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Model not found",
            )

        versions = await self.repository.get_by_model_id(model_id)
        return [ModelVersionResponse.model_validate(version) for version in versions]

    async def update_version_status(
        self, version_id: int, status: ModelVersionStatus, user_id: int
    ) -> ModelVersionResponse:
        """
        Update a model version status.

        Args:
            version_id: Version ID
            status: New status
            user_id: User ID (for ownership verification)

        Returns:
            Updated model version response

        Raises:
            HTTPException: If version not found or not owned by user
        """
        version = await self.repository.get_by_id(version_id)
        if not version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Model version not found",
            )

        # Verify ownership
        model = await self.model_repository.get_by_id(version.model_id, user_id)
        if not model:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied",
            )

        version.status = status
        updated_version = await self.repository.update(version)
        return ModelVersionResponse.model_validate(updated_version)

    async def update_version_s3_path(
        self, version_id: int, s3_path: str, user_id: int
    ) -> ModelVersionResponse:
        """
        Update a model version S3 path.

        Args:
            version_id: Version ID
            s3_path: New S3 path
            user_id: User ID (for ownership verification)

        Returns:
            Updated model version response

        Raises:
            HTTPException: If version not found or not owned by user
        """
        version = await self.repository.get_by_id(version_id)
        if not version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Model version not found",
            )

        # Verify ownership
        model = await self.model_repository.get_by_id(version.model_id, user_id)
        if not model:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied",
            )

        version.s3_path = s3_path
        updated_version = await self.repository.update(version)
        return ModelVersionResponse.model_validate(updated_version)


class DeploymentService:
    """Service for deployment business logic operations."""

    def __init__(self, db: AsyncSession):
        """
        Initialize deployment service.

        Args:
            db: Database session
        """
        self.repository = DeploymentRepository(db)
        self.version_repository = ModelVersionRepository(db)
        self.model_repository = ModelRepository(db)

    async def create_deployment(
        self, deployment_data: DeploymentCreate, user_id: int
    ) -> DeploymentResponse:
        """
        Create a new deployment with business logic validation.

        Args:
            deployment_data: Deployment creation data
            user_id: User ID (for ownership verification)

        Returns:
            Created deployment response

        Raises:
            HTTPException: If version not found or validation fails
        """
        # Business rule: Verify version exists and belongs to user
        version = await self.version_repository.get_by_id(deployment_data.version_id)
        if not version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Model version not found",
            )

        # Verify ownership through model
        model = await self.model_repository.get_by_id(version.model_id, user_id)
        if not model:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied",
            )

        # Business rule: Version must be READY before deployment
        if version.status != ModelVersionStatus.READY:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot deploy version with status '{version.status}'. Version must be READY.",
            )

        # Create deployment (k8s_service_name will be generated in repository)
        deployment = await self.repository.create(deployment_data)

        return DeploymentResponse.model_validate(deployment)

    async def get_deployment(
        self, deployment_id: int, user_id: int
    ) -> DeploymentResponse:
        """
        Get a deployment by ID, ensuring ownership.

        Args:
            deployment_id: Deployment ID
            user_id: User ID (for ownership verification)

        Returns:
            Deployment response

        Raises:
            HTTPException: If deployment not found or not owned by user
        """
        deployment = await self.repository.get_by_id(deployment_id)
        if not deployment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Deployment not found",
            )

        # Verify ownership through version -> model
        version = await self.version_repository.get_by_id(deployment.version_id)
        if not version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Model version not found",
            )

        model = await self.model_repository.get_by_id(version.model_id, user_id)
        if not model:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied",
            )

        return DeploymentResponse.model_validate(deployment)

    async def get_deployments_by_version(
        self, version_id: int, user_id: int
    ) -> List[DeploymentResponse]:
        """
        Get all deployments for a model version, ensuring ownership.

        Args:
            version_id: Version ID
            user_id: User ID (for ownership verification)

        Returns:
            List of deployment responses

        Raises:
            HTTPException: If version not found or not owned by user
        """
        # Verify ownership
        version = await self.version_repository.get_by_id(version_id)
        if not version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Model version not found",
            )

        model = await self.model_repository.get_by_id(version.model_id, user_id)
        if not model:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied",
            )

        deployments = await self.repository.get_by_version_id(version_id)
        return [
            DeploymentResponse.model_validate(deployment) for deployment in deployments
        ]

    async def delete_deployment(self, deployment_id: int, user_id: int) -> None:
        """
        Delete a deployment, ensuring ownership.

        Args:
            deployment_id: Deployment ID
            user_id: User ID (for ownership verification)

        Raises:
            HTTPException: If deployment not found or not owned by user
        """
        deployment = await self.repository.get_by_id(deployment_id)
        if not deployment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Deployment not found",
            )

        # Verify ownership
        version = await self.version_repository.get_by_id(deployment.version_id)
        if not version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Model version not found",
            )

        model = await self.model_repository.get_by_id(version.model_id, user_id)
        if not model:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied",
            )

        await self.repository.delete(deployment)

