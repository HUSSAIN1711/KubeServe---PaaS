"""
Model registry API routes.
Handles model, model version, and deployment operations.
"""

from typing import List
from fastapi import APIRouter, Depends, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.model import (
    ModelCreate,
    ModelResponse,
    ModelVersionCreate,
    ModelVersionResponse,
    DeploymentCreate,
    DeploymentResponse,
)
from app.services.model_service import (
    ModelService,
    ModelVersionService,
    DeploymentService,
)
from app.services.storage_service import StorageService
from app.core.dependencies import get_current_active_user
from app.schemas.user import UserResponse
from app.models.model import ModelVersionStatus

router = APIRouter()


# Model Routes
@router.post("/models", response_model=ModelResponse, status_code=status.HTTP_201_CREATED)
async def create_model(
    model_data: ModelCreate,
    current_user: UserResponse = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new model.

    Args:
        model_data: Model creation data
        current_user: Current authenticated user
        db: Database session

    Returns:
        Created model response
    """
    service = ModelService(db)
    return await service.create_model(model_data, current_user.id)


@router.get("/models", response_model=List[ModelResponse])
async def get_models(
    current_user: UserResponse = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all models for the current user.

    Args:
        current_user: Current authenticated user
        db: Database session

    Returns:
        List of model responses
    """
    service = ModelService(db)
    return await service.get_all_models(current_user.id)


@router.get("/models/{model_id}", response_model=ModelResponse)
async def get_model(
    model_id: int,
    current_user: UserResponse = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get a model by ID.

    Args:
        model_id: Model ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        Model response
    """
    service = ModelService(db)
    return await service.get_model(model_id, current_user.id)


@router.delete("/models/{model_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_model(
    model_id: int,
    current_user: UserResponse = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a model.

    Args:
        model_id: Model ID
        current_user: Current authenticated user
        db: Database session
    """
    service = ModelService(db)
    await service.delete_model(model_id, current_user.id)


# Model Version Routes
@router.post(
    "/models/{model_id}/versions",
    response_model=ModelVersionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_model_version(
    model_id: int,
    version_data: ModelVersionCreate,
    current_user: UserResponse = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new model version.

    Args:
        model_id: Model ID
        version_data: Model version creation data
        current_user: Current authenticated user
        db: Database session

    Returns:
        Created model version response
    """
    # Ensure model_id in path matches version_data
    version_data.model_id = model_id

    service = ModelVersionService(db)
    return await service.create_version(version_data, current_user.id)


@router.get(
    "/models/{model_id}/versions", response_model=List[ModelVersionResponse]
)
async def get_model_versions(
    model_id: int,
    current_user: UserResponse = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all versions for a model.

    Args:
        model_id: Model ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        List of model version responses
    """
    service = ModelVersionService(db)
    return await service.get_versions_by_model(model_id, current_user.id)


@router.get("/versions/{version_id}", response_model=ModelVersionResponse)
async def get_model_version(
    version_id: int,
    current_user: UserResponse = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get a model version by ID.

    Args:
        version_id: Version ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        Model version response
    """
    service = ModelVersionService(db)
    return await service.get_version(version_id, current_user.id)


@router.patch("/versions/{version_id}/status", response_model=ModelVersionResponse)
async def update_version_status(
    version_id: int,
    status: ModelVersionStatus,
    current_user: UserResponse = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update a model version status.

    Args:
        version_id: Version ID
        status: New status
        current_user: Current authenticated user
        db: Database session

    Returns:
        Updated model version response
    """
    service = ModelVersionService(db)
    return await service.update_version_status(version_id, status, current_user.id)


@router.post(
    "/versions/{version_id}/upload",
    response_model=ModelVersionResponse,
    status_code=status.HTTP_200_OK,
)
async def upload_model_artifacts(
    version_id: int,
    file: UploadFile = File(..., description="Model file (e.g., model.joblib)", alias="model_file"),
    requirements: UploadFile = File(..., description="Requirements file (requirements.txt)", alias="requirements_file"),
    current_user: UserResponse = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload model artifacts (model file and requirements.txt) for a version.

    Args:
        version_id: Version ID
        model_file: Model file (joblib, pkl, or pickle)
        requirements_file: Requirements.txt file
        current_user: Current authenticated user
        db: Database session

    Returns:
        Updated model version response with s3_path
    """
    # Verify version exists and user owns it
    version_service = ModelVersionService(db)
    version = await version_service.get_version(version_id, current_user.id)
    
    # Get model to get model name
    model_service = ModelService(db)
    model = await model_service.get_model(version.model_id, current_user.id)
    
    # Upload files to S3
    storage_service = StorageService()
    model_s3_path, requirements_s3_path = await storage_service.upload_model_artifacts(
        user_id=current_user.id,
        model_name=model.name,
        version_tag=version.version_tag,
        model_file=file,
        requirements_file=requirements,
    )
    
    # Update version with model S3 path (we store the model path, requirements is implicit)
    # The s3_path in the database represents the model file path
    updated_version = await version_service.update_version_s3_path(
        version_id, model_s3_path, current_user.id
    )
    
    return updated_version


# Deployment Routes
@router.post(
    "/versions/{version_id}/deployments",
    response_model=DeploymentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_deployment(
    version_id: int,
    deployment_data: DeploymentCreate,
    current_user: UserResponse = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new deployment for a model version.

    Args:
        version_id: Version ID
        deployment_data: Deployment creation data
        current_user: Current authenticated user
        db: Database session

    Returns:
        Created deployment response
    """
    # Ensure version_id in path matches deployment_data
    deployment_data.version_id = version_id

    service = DeploymentService(db)
    return await service.create_deployment(deployment_data, current_user.id)


@router.get(
    "/versions/{version_id}/deployments", response_model=List[DeploymentResponse]
)
async def get_deployments(
    version_id: int,
    current_user: UserResponse = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all deployments for a model version.

    Args:
        version_id: Version ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        List of deployment responses
    """
    service = DeploymentService(db)
    return await service.get_deployments_by_version(version_id, current_user.id)


@router.get("/deployments/{deployment_id}", response_model=DeploymentResponse)
async def get_deployment(
    deployment_id: int,
    current_user: UserResponse = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get a deployment by ID.

    Args:
        deployment_id: Deployment ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        Deployment response
    """
    service = DeploymentService(db)
    return await service.get_deployment(deployment_id, current_user.id)


@router.delete("/deployments/{deployment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_deployment(
    deployment_id: int,
    current_user: UserResponse = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a deployment.

    Args:
        deployment_id: Deployment ID
        current_user: Current authenticated user
        db: Database session
    """
    service = DeploymentService(db)
    await service.delete_deployment(deployment_id, current_user.id)

