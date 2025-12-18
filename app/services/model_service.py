"""
Model service containing business logic for model operations.
"""

import logging
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
    DeploymentUpdate,
)
from app.models.model import ModelVersionStatus
from app.services.deployment_service import HelmDeploymentService
from app.config import settings

logger = logging.getLogger(__name__)


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
        self.helm_service = HelmDeploymentService()

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

        # Business rule: Version must have S3 path
        if not version.s3_path:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Model version must have an S3 path. Please upload the model first.",
            )

        # Create deployment record in database first (to get deployment.id)
        deployment = await self.repository.create(deployment_data)

        # Deploy to Kubernetes using Helm
        namespace = f"user-{user_id}"
        release_name = deployment.k8s_service_name  # Use the generated service name as release name
        
        try:
            # Parse S3 path to extract bucket and key
            # Format: s3://bucket/path/to/model.joblib or bucket/path/to/model.joblib
            s3_path = version.s3_path
            if s3_path.startswith("s3://"):
                s3_path = s3_path[5:]  # Remove s3:// prefix
            
            # Split into bucket and key
            parts = s3_path.split("/", 1)
            s3_bucket = parts[0] if len(parts) > 0 else settings.MINIO_BUCKET_NAME
            s3_key = parts[1] if len(parts) > 1 else ""
            
            # Full S3 path for Helm
            full_s3_path = f"s3://{s3_bucket}/{s3_key}" if s3_key else f"s3://{s3_bucket}/"
            
            # Determine S3 endpoint (use internal service name for Kubernetes)
            # For local dev, use minio:9000 (internal to cluster)
            # For external, use settings.MINIO_ENDPOINT
            s3_endpoint = "minio:9000"  # Internal cluster endpoint
            
            # Deploy using Helm with deployment_id in the ingress path
            deployment_info = self.helm_service.deploy_model(
                release_name=release_name,
                namespace=namespace,
                s3_path=full_s3_path,
                s3_endpoint=s3_endpoint,
                s3_access_key=settings.MINIO_ACCESS_KEY,
                s3_secret_key=settings.MINIO_SECRET_KEY,
                s3_bucket=s3_bucket,
                s3_use_ssl=settings.MINIO_USE_SSL,
                replicas=deployment_data.replicas,
                ingress_enabled=True,
                ingress_host=settings.INGRESS_HOST,
                ingress_path=f"{settings.INGRESS_BASE_PATH}/{deployment.id}"  # Use deployment.id in path
            )
            
            # Update deployment with URL (using deployment.id)
            deployment.url = f"http://{settings.INGRESS_HOST}:30080{settings.INGRESS_BASE_PATH}/{deployment.id}"
            deployment = await self.repository.update(deployment)
            
            logger.info(f"Successfully deployed model version {version.id} as deployment {deployment.id}")
            
        except Exception as e:
            # If Helm deployment fails, delete the database record
            await self.repository.delete(deployment)
            logger.error(f"Failed to deploy model version {version.id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to deploy model to Kubernetes: {str(e)}"
            )

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

        # Undeploy from Kubernetes using Helm
        namespace = f"user-{user_id}"
        release_name = deployment.k8s_service_name
        
        try:
            self.helm_service.undeploy_model(
                release_name=release_name,
                namespace=namespace
            )
            logger.info(f"Successfully undeployed model deployment {deployment.id}")
        except Exception as e:
            # Log error but continue with database deletion
            # This allows cleanup even if Helm uninstall fails
            logger.warning(f"Failed to undeploy Helm release {release_name}: {str(e)}. Continuing with database cleanup.")

        # Delete deployment record from database
        await self.repository.delete(deployment)

