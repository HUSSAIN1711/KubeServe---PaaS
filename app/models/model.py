"""
Model registry database models.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class ModelType(str, enum.Enum):
    """Model type enumeration."""
    SKLEARN = "sklearn"
    PYTORCH = "pytorch"


class ModelVersionStatus(str, enum.Enum):
    """Model version status enumeration."""
    BUILDING = "Building"
    READY = "Ready"
    FAILED = "Failed"


class Model(Base):
    """Model metadata model representing a user's ML model."""

    __tablename__ = "models"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String, nullable=False)
    type = Column(Enum(ModelType), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="models")
    versions = relationship("ModelVersion", back_populates="model", cascade="all, delete-orphan")


class ModelVersion(Base):
    """Model version model representing a specific version of a model."""

    __tablename__ = "model_versions"

    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(Integer, ForeignKey("models.id", ondelete="CASCADE"), nullable=False, index=True)
    version_tag = Column(String, nullable=False)  # e.g., "v1", "v2", "latest"
    s3_path = Column(String, nullable=False)  # Path to model artifact in S3
    status = Column(Enum(ModelVersionStatus), default=ModelVersionStatus.BUILDING, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    model = relationship("Model", back_populates="versions")
    deployments = relationship("Deployment", back_populates="model_version", cascade="all, delete-orphan")


class Deployment(Base):
    """Deployment model representing a deployed model version."""

    __tablename__ = "deployments"

    id = Column(Integer, primary_key=True, index=True)
    version_id = Column(Integer, ForeignKey("model_versions.id", ondelete="CASCADE"), nullable=False, index=True)
    k8s_service_name = Column(String, nullable=False, unique=True)  # Kubernetes service name
    url = Column(String, nullable=True)  # Public URL for the deployment
    replicas = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    model_version = relationship("ModelVersion", back_populates="deployments")

