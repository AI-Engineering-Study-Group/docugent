"""Authentication dependencies for FastAPI."""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import User, Role
from app.services.auth_service import auth_service


security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get the current authenticated user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Verify token
    payload = auth_service.verify_token(credentials.credentials, "access")
    if payload is None:
        raise credentials_exception
    
    # Check if token is blacklisted
    is_blacklisted = await auth_service.is_token_blacklisted(db, credentials.credentials)
    if is_blacklisted:
        raise credentials_exception
    
    # Get user
    user_id = payload.get("user_id")
    if user_id is None:
        raise credentials_exception
    
    result = await db.execute(
        select(User)
        .options(selectinload(User.role), selectinload(User.auth))
        .where(User.id == user_id, User.is_active == True)
    )
    user = result.scalar_one_or_none()
    
    if user is None:
        raise credentials_exception
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get the current active user."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


def require_role(required_role: str):
    """Dependency factory for role-based access control."""
    def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role.name != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role: {required_role}"
            )
        return current_user
    return role_checker


def require_any_role(*required_roles: str):
    """Dependency factory for multiple role access control."""
    def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role.name not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {', '.join(required_roles)}"
            )
        return current_user
    return role_checker


# Common role dependencies
require_admin = require_role("admin")
require_moderator = require_any_role("admin", "moderator")
require_user = require_any_role("admin", "moderator", "user")
