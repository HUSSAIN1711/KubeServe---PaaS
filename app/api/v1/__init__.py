"""
API v1 routes package.
"""

from fastapi import APIRouter

router = APIRouter()

# Import and include route modules here
from app.api.v1 import auth  # noqa: E402
from app.api.v1 import me  # noqa: E402
from app.api.v1 import models  # noqa: E402

router.include_router(auth.router, prefix="/auth", tags=["authentication"])
router.include_router(me.router, tags=["users"])
router.include_router(models.router, tags=["models"])

