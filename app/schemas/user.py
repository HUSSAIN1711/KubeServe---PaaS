"""
User Pydantic schemas for request/response validation.
"""

from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, ConfigDict

from app.models.user import UserRole


class UserCreate(BaseModel):
    """Schema for creating a new user."""

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password (min 8 characters)")
    role: UserRole = Field(default=UserRole.USER, description="User role")


class UserResponse(BaseModel):
    """Schema for user response (excludes sensitive data)."""

    model_config = ConfigDict(
        from_attributes=True,
        protected_namespaces=(),
    )

    id: int
    email: str
    role: UserRole
    created_at: datetime
    updated_at: datetime


class UserLogin(BaseModel):
    """Schema for user login."""

    email: EmailStr
    password: str


class Token(BaseModel):
    """Schema for JWT token response."""

    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Schema for token payload data."""

    user_id: int | None = None
    email: str | None = None

