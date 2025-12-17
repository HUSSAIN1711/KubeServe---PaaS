"""
Current user endpoints.
Example of protected routes using authentication dependency.
"""

from fastapi import APIRouter, Depends
from app.schemas.user import UserResponse
from app.core.dependencies import get_current_active_user

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: UserResponse = Depends(get_current_active_user)
):
    """
    Get current authenticated user information.

    Args:
        current_user: Current authenticated user from dependency

    Returns:
        Current user information
    """
    return current_user

