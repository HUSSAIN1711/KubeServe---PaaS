"""
Model registry Pydantic schemas for request/response validation.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict

from app.models.model import ModelType, ModelVersionStatus


# Model Schemas
class ModelBase(BaseModel):
    """Base schema for model operations."""

    name: str = Field(..., min_length=1, max_length=100, description="Model name")
    type: ModelType = Field(..., description="Model type (sklearn/pytorch)")


class ModelCreate(ModelBase):
    """Schema for creating a new model."""

    pass


class ModelUpdate(BaseModel):
    """Schema for updating a model."""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    type: Optional[ModelType] = None


class ModelResponse(ModelBase):
    """Schema for model response."""

    model_config = ConfigDict(
        from_attributes=True,
        protected_namespaces=(),
    )
    
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime


class ModelWithVersions(ModelResponse):
    """Schema for model with versions."""

    versions: List["ModelVersionResponse"] = []


# ModelVersion Schemas
class ModelVersionBase(BaseModel):
    """Base schema for model version operations."""

    version_tag: str = Field(..., min_length=1, max_length=50, description="Version tag (e.g., v1, v2)")
    s3_path: str = Field(..., description="S3 path to model artifact")


class ModelVersionCreate(ModelVersionBase):
    """Schema for creating a new model version.
    
    Note: model_id is set from the path parameter in the route,
    so it's optional in the request body.
    """

    model_config = ConfigDict(protected_namespaces=())
    
    model_id: Optional[int] = Field(None, description="ID of the parent model (set from path)")


class ModelVersionUpdate(BaseModel):
    """Schema for updating a model version."""

    status: Optional[ModelVersionStatus] = None
    s3_path: Optional[str] = None


class ModelVersionResponse(ModelVersionBase):
    """Schema for model version response."""

    model_config = ConfigDict(
        from_attributes=True,
        protected_namespaces=(),
    )
    
    id: int
    model_id: int
    status: ModelVersionStatus
    created_at: datetime
    updated_at: datetime


class ModelVersionWithModel(ModelVersionResponse):
    """Schema for model version with model information."""

    model_config = ConfigDict(protected_namespaces=())
    
    model: ModelResponse


# Deployment Schemas
class DeploymentBase(BaseModel):
    """Base schema for deployment operations."""

    replicas: int = Field(default=1, ge=1, le=10, description="Number of replicas")


class DeploymentCreate(DeploymentBase):
    """Schema for creating a new deployment.
    
    Note: version_id is set from the path parameter in the route,
    so it's optional in the request body.
    """

    version_id: Optional[int] = Field(None, description="ID of the model version to deploy (set from path)")


class DeploymentUpdate(BaseModel):
    """Schema for updating a deployment."""

    replicas: Optional[int] = Field(None, ge=1, le=10)
    url: Optional[str] = None


class DeploymentResponse(DeploymentBase):
    """Schema for deployment response."""

    model_config = ConfigDict(
        from_attributes=True,
        protected_namespaces=(),
    )
    
    id: int
    version_id: int
    k8s_service_name: str
    url: Optional[str]
    created_at: datetime
    updated_at: datetime


class DeploymentWithVersion(DeploymentResponse):
    """Schema for deployment with model version information."""

    model_config = ConfigDict(protected_namespaces=())
    
    model_version: ModelVersionResponse


# Update forward references for nested models
ModelWithVersions.model_rebuild()
ModelVersionWithModel.model_rebuild()
DeploymentWithVersion.model_rebuild()

