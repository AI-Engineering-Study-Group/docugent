"""
FastAPI router for agent endpoints.
"""

from fastapi import APIRouter, HTTPException, status, Header
import time

from app.config.logger import Logger
from app.schemas.base import SuccessResponseSchema
from app.config.settings import settings
from app.services.redis_service import RedisService

router = APIRouter()
logger = Logger.get_logger(__name__)

# Track agent startup time
startup_time = time.time()

@router.post(
    "/cache/invalidate",
    response_model=SuccessResponseSchema[dict],
    status_code=status.HTTP_200_OK,
    summary="Invalidate Redis cache",
    description="Clear the entire Redis cache. Requires a valid secret key."
)
async def invalidate_cache(
    x_secret_key: str = Header(..., description="Secret key for authorization")
):
    """Invalidate the Redis cache."""
    if x_secret_key != settings.secret_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid secret key"
        )
    
    try:
        redis_service = RedisService.get_instance()
        result = redis_service.clear_cache()
        return SuccessResponseSchema(
            data=result,
            message="Cache invalidated successfully"
        )
    except Exception as e:
        logger.error(f"Error invalidating cache: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to invalidate cache"
        )

@router.get(
    "/cache/stats",
    response_model=SuccessResponseSchema[dict],
    status_code=status.HTTP_200_OK,
    summary="Get Redis cache statistics",
    description="Get statistics about the Redis cache. Requires a valid secret key."
)
async def get_cache_stats(
    x_secret_key: str = Header(..., description="Secret key for authorization")
):
    """Get Redis cache statistics."""
    if x_secret_key != settings.secret_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid secret key"
        )
    
    try:
        redis_service = RedisService.get_instance()
        stats = redis_service.get_stats()
        return SuccessResponseSchema(
            data=stats,
            message="Cache stats retrieved successfully"
        )
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get cache stats"
        )
