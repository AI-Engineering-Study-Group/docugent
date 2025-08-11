"""User management API routes."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import User, Role
from app.schemas.auth import (
    UserResponse,
    UserUpdateRequest,
    UserSuccessResponse,
    UsersListResponse
)
from app.schemas.base import SuccessResponseSchema
from app.dependencies.auth import require_admin, require_moderator, get_current_active_user


router = APIRouter()


@router.get("/", response_model=UsersListResponse)
async def get_all_users(
    skip: int = Query(0, ge=0, description="Number of users to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of users to return"),
    role_id: Optional[int] = Query(None, description="Filter by role ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search by name or email"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_moderator)
):
    """Get all users with optional filtering. Requires moderator or admin access."""
    query = select(User).options(selectinload(User.role))
    
    # Apply filters
    filters = []
    if role_id is not None:
        filters.append(User.role_id == role_id)
    if is_active is not None:
        filters.append(User.is_active == is_active)
    if search:
        search_filter = f"%{search.lower()}%"
        filters.append(
            User.email.ilike(search_filter) |
            User.first_name.ilike(search_filter) |
            User.last_name.ilike(search_filter)
        )
    
    if filters:
        query = query.where(and_(*filters))
    
    # Apply pagination and ordering
    query = query.order_by(User.created_at.desc()).offset(skip).limit(limit)
    
    result = await db.execute(query)
    users = result.scalars().all()
    
    return SuccessResponseSchema(
        data=list(users),
        message=f"Retrieved {len(users)} users"
    )


@router.get("/{user_id}", response_model=UserSuccessResponse)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a single user by ID. Users can only access their own data unless they're moderator/admin."""
    # Check permissions
    if current_user.id != user_id and current_user.role.name not in ["admin", "moderator"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only access your own user information"
        )
    
    result = await db.execute(
        select(User).options(selectinload(User.role)).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    return SuccessResponseSchema(
        data=user,
        message="User retrieved successfully"
    )


@router.put("/{user_id}", response_model=UserSuccessResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update a user. Users can only update their own data unless they're moderator/admin."""
    # Check permissions
    if current_user.id != user_id and current_user.role.name not in ["admin", "moderator"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own user information"
        )
    
    # Get existing user
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    # Update fields
    if user_data.first_name is not None:
        user.first_name = user_data.first_name
    if user_data.last_name is not None:
        user.last_name = user_data.last_name
    if user_data.phone_number is not None:
        user.phone_number = user_data.phone_number
    
    await db.commit()
    # Ensure role is loaded for response
    await db.refresh(user, attribute_names=["role"])
    
    return SuccessResponseSchema(
        data=user,
        message="User updated successfully"
    )


@router.patch("/{user_id}/activate")
async def activate_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Activate a user. Requires admin access."""
    result = await db.execute(select(User).options(selectinload(User.role)).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    user.is_active = True
    await db.commit()
    
    return SuccessResponseSchema(
        data=None,
        message=f"User {user.email} activated successfully"
    )


@router.patch("/{user_id}/deactivate")
async def deactivate_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Deactivate a user. Requires admin access."""
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot deactivate your own account"
        )
    
    result = await db.execute(select(User).options(selectinload(User.role)).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    user.is_active = False
    await db.commit()
    
    return SuccessResponseSchema(
        data=None,
        message=f"User {user.email} deactivated successfully"
    )


@router.patch("/{user_id}/role")
async def change_user_role(
    user_id: int,
    role_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Change a user's role. Requires admin access."""
    # Get user
    result = await db.execute(select(User).options(selectinload(User.role)).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    # Check if role exists
    result = await db.execute(select(Role).where(Role.id == role_id, Role.is_active == True))
    role = result.scalar_one_or_none()
    
    if not role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Role with ID {role_id} not found or inactive"
        )
    
    # Update role
    user.role_id = role_id
    await db.commit()
    await db.refresh(user, attribute_names=["role"])
    
    return SuccessResponseSchema(
        data=user,
        message=f"User {user.email} role changed to {role.name}"
    )
