"""
FastAPI router for agent endpoints.
"""

from fastapi import APIRouter, HTTPException, status, Request, Query, Body, Header
from fastapi.responses import JSONResponse
from typing import Optional
import time

from app.config.logger import Logger
from app.schemas.base import SuccessResponseSchema, ErrorResponseSchema
from app.schemas.agents import AgentRequest, AgentResponse, AgentStatus
from app.agents.agent_api import process_user_message, get_agent_status
from app.config.settings import settings
from app.services.redis_service import RedisService

router = APIRouter()
logger = Logger.get_logger(__name__)

# Track agent startup time
startup_time = time.time()

@router.post(
    "/chat",
    response_model=SuccessResponseSchema[AgentResponse],
    status_code=status.HTTP_200_OK,
    summary="Chat with the API Conference AI Agent",
    description="Send a message to the AI agent and get a response"
)
async def chat_with_agent(
    request: AgentRequest,
    http_request: Request
):
    """Chat endpoint for interacting with the AI agent."""
    try:
        logger.info(f"Processing chat request from {request.user_id}")
        
        # Process the message
        result = await process_user_message(
            user_input=request.message,
            user_id=request.user_id,
            session_id=request.session_id,
            timestamp=request.timestamp,
            timezone_offset=request.timezone_offset
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("fallback_message", "Agent processing failed")
            )
        
        # Extract response
        agent_response = result["response"]
        
        # Create response object
        response_data = AgentResponse(
            response=agent_response,
            user_id=request.user_id,
            session_id=request.session_id,
            tools_used=result.get("tools_used"),
            confidence=result.get("confidence"),
            metadata=result.get("metadata")
        )
        
        return SuccessResponseSchema(
            data=response_data,
            message="Message processed successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error. Please contact {settings.support_phone} for assistance."
        )

@router.get(
    "/status",
    response_model=SuccessResponseSchema[AgentStatus],
    status_code=status.HTTP_200_OK,
    summary="Get agent status",
    description="Get the current status of the AI agent"
)
async def get_agent_status_endpoint():
    """Get the current status of the AI agent."""
    try:
        # Get status from agent
        agent_status = get_agent_status()
        
        if agent_status.get("status") == "error":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get agent status"
            )
        
        uptime_seconds = time.time() - startup_time
        uptime_hours = uptime_seconds / 3600
        
        status_data = AgentStatus(
            status=agent_status.get("status", "operational"),
            uptime=f"{uptime_hours:.1f} hours"
        )
        
        return SuccessResponseSchema(
            data=status_data,
            message="Agent status retrieved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting agent status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get agent status"
        )

@router.get(
    "/health",
    response_model=SuccessResponseSchema[dict],
    status_code=status.HTTP_200_OK,
    summary="Health check",
    description="Check if the agent service is healthy"
)
async def health_check():
    """Health check endpoint."""
    try:
        health_data = {
            "status": "healthy",
            "service": "apiconf-agent",
            "version": "0.1.0",
            "environment": settings.environment,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        return SuccessResponseSchema(
            data=health_data,
            message="Service is healthy"
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service is unhealthy"
        )

@router.get(
    "/info",
    response_model=SuccessResponseSchema[dict],
    status_code=status.HTTP_200_OK,
    summary="Get conference information",
    description="Get basic information about the API Conference"
)
async def get_conference_info():
    """Get basic conference information."""
    try:
        info_data = {
            "venue": {
                "name": settings.conference_venue_name,
                "address": settings.conference_venue_address,
                "coordinates": settings.conference_venue_coordinates
            },
            "support": {
                "phone": settings.support_phone,
                "email": settings.support_email
            },
            "agent_capabilities": [
                "Navigation and transportation assistance",
                "Speaker information and search",
                "Schedule management and recommendations",
                "General conference support",
                "Web scraping for real-time updates"
            ]
        }
        
        return SuccessResponseSchema(
            data=info_data,
            message="Conference information retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Error getting conference info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get conference information"
        ) 

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
