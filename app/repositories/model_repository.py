"""
Model repository for database operations.
Handles all database queries related to models, model versions, and deployments.
"""

from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.model import Model, ModelVersion, Deployment, ModelVersionStatus
from app.schemas.model import ModelCreate, ModelVersionCreate, DeploymentCreate


class ModelRepository:
    """Repository for model data access operations."""

    def __init__(self, db: AsyncSession):
        """
        Initialize model repository.

        Args:
            db: Database session
        """
        self.db = db

    async def get_by_id(self, model_id: int, user_id: int) -> Optional[Model]:
        """
        Get a model by ID, ensuring it belongs to the user.

        Args:
            model_id: The model ID
            user_id: The user ID (for ownership verification)

        Returns:
            Model object if found and owned by user, None otherwise
        """
        result = await self.db.execute(
            select(Model).where(Model.id == model_id, Model.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_all_by_user(self, user_id: int) -> List[Model]:
        """
        Get all models for a user.

        Args:
            user_id: The user ID

        Returns:
            List of Model objects
        """
        result = await self.db.execute(select(Model).where(Model.user_id == user_id))
        return list(result.scalars().all())

    async def create(self, model_data: ModelCreate, user_id: int) -> Model:
        """
        Create a new model.

        Args:
            model_data: Model creation data
            user_id: The user ID who owns the model

        Returns:
            Created Model object
        """
        model = Model(
            name=model_data.name,
            type=model_data.type,
            user_id=user_id,
        )
        self.db.add(model)
        await self.db.commit()
        await self.db.refresh(model)
        return model

    async def update(self, model: Model) -> Model:
        """
        Update an existing model.

        Args:
            model: Model object to update

        Returns:
            Updated Model object
        """
        await self.db.commit()
        await self.db.refresh(model)
        return model

    async def delete(self, model: Model) -> None:
        """
        Delete a model.

        Args:
            model: Model object to delete
        """
        await self.db.delete(model)
        await self.db.commit()


class ModelVersionRepository:
    """Repository for model version data access operations."""

    def __init__(self, db: AsyncSession):
        """
        Initialize model version repository.

        Args:
            db: Database session
        """
        self.db = db

    async def get_by_id(self, version_id: int) -> Optional[ModelVersion]:
        """
        Get a model version by ID.

        Args:
            version_id: The version ID

        Returns:
            ModelVersion object if found, None otherwise
        """
        result = await self.db.execute(
            select(ModelVersion).where(ModelVersion.id == version_id)
        )
        return result.scalar_one_or_none()

    async def get_by_model_id(self, model_id: int) -> List[ModelVersion]:
        """
        Get all versions for a model.

        Args:
            model_id: The model ID

        Returns:
            List of ModelVersion objects
        """
        result = await self.db.execute(
            select(ModelVersion).where(ModelVersion.model_id == model_id)
        )
        return list(result.scalars().all())

    async def get_by_model_and_tag(
        self, model_id: int, version_tag: str
    ) -> Optional[ModelVersion]:
        """
        Get a model version by model ID and version tag.

        Args:
            model_id: The model ID
            version_tag: The version tag

        Returns:
            ModelVersion object if found, None otherwise
        """
        result = await self.db.execute(
            select(ModelVersion).where(
                ModelVersion.model_id == model_id,
                ModelVersion.version_tag == version_tag,
            )
        )
        return result.scalar_one_or_none()

    async def create(self, version_data: ModelVersionCreate) -> ModelVersion:
        """
        Create a new model version.

        Args:
            version_data: Model version creation data

        Returns:
            Created ModelVersion object
        """
        version = ModelVersion(
            model_id=version_data.model_id,
            version_tag=version_data.version_tag,
            s3_path=version_data.s3_path,
            status=ModelVersionStatus.BUILDING,
        )
        self.db.add(version)
        await self.db.commit()
        await self.db.refresh(version)
        return version

    async def update(self, version: ModelVersion) -> ModelVersion:
        """
        Update an existing model version.

        Args:
            version: ModelVersion object to update

        Returns:
            Updated ModelVersion object
        """
        await self.db.commit()
        await self.db.refresh(version)
        return version


class DeploymentRepository:
    """Repository for deployment data access operations."""

    def __init__(self, db: AsyncSession):
        """
        Initialize deployment repository.

        Args:
            db: Database session
        """
        self.db = db

    async def get_by_id(self, deployment_id: int) -> Optional[Deployment]:
        """
        Get a deployment by ID.

        Args:
            deployment_id: The deployment ID

        Returns:
            Deployment object if found, None otherwise
        """
        result = await self.db.execute(
            select(Deployment).where(Deployment.id == deployment_id)
        )
        return result.scalar_one_or_none()

    async def get_by_version_id(self, version_id: int) -> List[Deployment]:
        """
        Get all deployments for a model version.

        Args:
            version_id: The version ID

        Returns:
            List of Deployment objects
        """
        result = await self.db.execute(
            select(Deployment).where(Deployment.version_id == version_id)
        )
        return list(result.scalars().all())

    async def get_by_k8s_service_name(
        self, k8s_service_name: str
    ) -> Optional[Deployment]:
        """
        Get a deployment by Kubernetes service name.

        Args:
            k8s_service_name: The Kubernetes service name

        Returns:
            Deployment object if found, None otherwise
        """
        result = await self.db.execute(
            select(Deployment).where(Deployment.k8s_service_name == k8s_service_name)
        )
        return result.scalar_one_or_none()

    async def create(self, deployment_data: DeploymentCreate) -> Deployment:
        """
        Create a new deployment.

        Args:
            deployment_data: Deployment creation data

        Returns:
            Created Deployment object
        """
        import time
        # Generate unique Kubernetes service name
        k8s_service_name = f"model-{deployment_data.version_id}-{int(time.time())}"
        
        deployment = Deployment(
            version_id=deployment_data.version_id,
            k8s_service_name=k8s_service_name,
            replicas=deployment_data.replicas,
        )
        self.db.add(deployment)
        await self.db.commit()
        await self.db.refresh(deployment)
        return deployment

    async def update(self, deployment: Deployment) -> Deployment:
        """
        Update an existing deployment.

        Args:
            deployment: Deployment object to update

        Returns:
            Updated Deployment object
        """
        await self.db.commit()
        await self.db.refresh(deployment)
        return deployment

    async def delete(self, deployment: Deployment) -> None:
        """
        Delete a deployment.

        Args:
            deployment: Deployment object to delete
        """
        await self.db.delete(deployment)
        await self.db.commit()

