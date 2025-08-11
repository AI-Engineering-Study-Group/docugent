"""Role management API routes."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import Role, User
from app.schemas.auth import (
    RoleResponse,
    RoleCreateRequest,
    RoleUpdateRequest,
    RoleSuccessResponse,
    RolesListResponse
)
from app.schemas.base import SuccessResponseSchema
from app.dependencies.auth import require_admin, get_current_active_user


router = APIRouter()


@router.post("/", response_model=RoleSuccessResponse, status_code=status.HTTP_201_CREATED)
async def create_role(
    role_data: RoleCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Create a new role. Requires admin access."""
    # Check if role name already exists
    result = await db.execute(select(Role).where(Role.name == role_data.name))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Role with name '{role_data.name}' already exists"
        )
    
    # Create role
    role = Role(
        name=role_data.name,
        description=role_data.description,
        permissions=role_data.permissions,
        is_active=role_data.is_active
    )
    db.add(role)
    await db.commit()
    await db.refresh(role)
    
    return SuccessResponseSchema(
        data=role,
        message=f"Role '{role.name}' created successfully"
    )


@router.get("/", response_model=RolesListResponse)
async def get_all_roles(
    include_inactive: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all roles. Include inactive roles with include_inactive=true."""
    query = select(Role)
    if not include_inactive:
        query = query.where(Role.is_active == True)
    
    result = await db.execute(query.order_by(Role.name))
    roles = result.scalars().all()
    
    return SuccessResponseSchema(
        data=list(roles),
        message="Roles retrieved successfully"
    )


@router.get("/{role_id}", response_model=RoleSuccessResponse)
async def get_role(
    role_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a single role by ID."""
    result = await db.execute(select(Role).where(Role.id == role_id))
    role = result.scalar_one_or_none()
    
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role with ID {role_id} not found"
        )
    
    return SuccessResponseSchema(
        data=role,
        message="Role retrieved successfully"
    )


@router.put("/{role_id}", response_model=RoleSuccessResponse)
async def update_role(
    role_id: int,
    role_data: RoleUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Update a role. Requires admin access."""
    # Get existing role
    result = await db.execute(select(Role).where(Role.id == role_id))
    role = result.scalar_one_or_none()
    
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role with ID {role_id} not found"
        )
    
    # Check if new name conflicts with existing role
    if role_data.name and role_data.name != role.name:
        result = await db.execute(select(Role).where(Role.name == role_data.name))
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Role with name '{role_data.name}' already exists"
            )
        role.name = role_data.name
    
    # Update other fields
    if role_data.description is not None:
        role.description = role_data.description
    if role_data.permissions is not None:
        role.permissions = role_data.permissions
    if role_data.is_active is not None:
        role.is_active = role_data.is_active
    
    await db.commit()
    await db.refresh(role)
    
    return SuccessResponseSchema(
        data=role,
        message=f"Role '{role.name}' updated successfully"
    )


@router.delete("/{role_id}")
async def delete_role(
    role_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Delete a role. Requires admin access."""
    # Get existing role
    result = await db.execute(select(Role).where(Role.id == role_id))
    role = result.scalar_one_or_none()
    
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role with ID {role_id} not found"
        )
    
    # Check if role is in use by any users
    result = await db.execute(select(User).where(User.role_id == role_id))
    users_with_role = result.scalars().all()
    
    if users_with_role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete role '{role.name}' because it is assigned to {len(users_with_role)} user(s)"
        )
    
    # Delete role
    await db.delete(role)
    await db.commit()
    
    return SuccessResponseSchema(
        data=None,
        message=f"Role '{role.name}' deleted successfully"
    )
