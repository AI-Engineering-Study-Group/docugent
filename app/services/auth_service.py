"""Authentication service for JWT and password management."""

import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.config.settings import settings
from app.models import User, Auth, Role, TokenBlacklist


class AuthService:
    """Service for handling authentication operations."""
    
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.algorithm = settings.jwt_algorithm
        self.secret_key = settings.secret_key
        self.access_token_expire_minutes = settings.access_token_expire_minutes
        self.refresh_token_expire_days = settings.refresh_token_expire_days
    
    def hash_password(self, password: str) -> tuple[str, str]:
        """Hash a password with salt."""
        salt = secrets.token_hex(16)
        hashed = self.pwd_context.hash(password + salt)
        return hashed, salt
    
    def verify_password(self, plain_password: str, hashed_password: str, salt: str) -> bool:
        """Verify a password against its hash."""
        return self.pwd_context.verify(plain_password + salt, hashed_password)
    
    def create_access_token(self, data: Dict[str, Any]) -> tuple[str, datetime]:
        """Create a JWT access token."""
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(minutes=self.access_token_expire_minutes)
        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt, expire
    
    def create_refresh_token(self, data: Dict[str, Any]) -> tuple[str, datetime]:
        """Create a JWT refresh token."""
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(days=self.refresh_token_expire_days)
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt, expire
    
    def verify_token(self, token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
        """Verify and decode a JWT token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # Check token type
            if payload.get("type") != token_type:
                return None
            
            # Check expiration
            exp = payload.get("exp")
            if exp and datetime.fromtimestamp(exp, tz=timezone.utc) < datetime.now(timezone.utc):
                return None
            
            return payload
        except JWTError:
            return None
    
    async def authenticate_user(self, db: AsyncSession, email: str, password: str) -> Optional[User]:
        """Authenticate a user with email and password."""
        # Get user with auth data
        result = await db.execute(
            select(User)
            .options(
                selectinload(User.auth),
                selectinload(User.role),
            )
            .where(User.email == email, User.is_active == True)
        )
        user = result.scalar_one_or_none()
        
        if not user or not user.auth:
            return None
        
        # Verify password
        if not self.verify_password(password, user.auth.hashed_password, user.auth.salt or ""):
            # Increment failed login attempts
            user.auth.failed_login_attempts += 1
            await db.commit()
            return None
        
        # Reset failed login attempts and update last login
        user.auth.failed_login_attempts = 0
        user.auth.last_login_at = datetime.now(timezone.utc).isoformat()
        await db.commit()
        
        return user
    
    async def create_tokens_for_user(self, db: AsyncSession, user: User) -> tuple[str, str, datetime]:
        """Create access and refresh tokens for a user."""
        # Ensure relationships are loaded to avoid async lazy-load
        result = await db.execute(
            select(User)
            .options(
                selectinload(User.auth),
                selectinload(User.role),
            )
            .where(User.id == user.id)
        )
        user = result.scalar_one()

        # Create token payload
        payload = {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role.name if getattr(user, "role", None) else "user",
            "user_id": user.id
        }
        
        # Create tokens
        access_token, access_expires = self.create_access_token(payload)
        refresh_token, refresh_expires = self.create_refresh_token(payload)
        
        # Store refresh token in auth table
        if user.auth is None:
            # In the unlikely event auth is not present, fetch it explicitly
            auth_result = await db.execute(select(Auth).where(Auth.user_id == user.id))
            auth = auth_result.scalar_one()
        else:
            auth = user.auth

        auth.refresh_token = refresh_token
        auth.refresh_token_expires_at = refresh_expires.isoformat()
        await db.commit()
        
        return access_token, refresh_token, access_expires
    
    async def refresh_access_token(self, db: AsyncSession, refresh_token: str) -> Optional[tuple[str, str, datetime]]:
        """Refresh an access token using a refresh token."""
        # Verify refresh token
        payload = self.verify_token(refresh_token, "refresh")
        if not payload:
            return None
        
        # Check if token is blacklisted
        result = await db.execute(
            select(TokenBlacklist).where(TokenBlacklist.token == refresh_token)
        )
        if result.scalar_one_or_none():
            return None
        
        # Get user
        user_id = payload.get("user_id")
        result = await db.execute(
            select(User)
            .options(selectinload(User.auth), selectinload(User.role))
            .where(User.id == user_id, User.is_active == True)
        )
        user = result.scalar_one_or_none()
        
        if not user or not user.auth:
            return None
        
        # Check if refresh token matches stored token
        if user.auth.refresh_token != refresh_token:
            return None
        
        # Create new tokens
        return await self.create_tokens_for_user(db, user)
    
    async def blacklist_token(self, db: AsyncSession, token: str, token_type: str, user_id: int, reason: str = "logout"):
        """Blacklist a token."""
        # Verify token to get expiration
        payload = self.verify_token(token, token_type)
        if not payload:
            return False
        
        exp = payload.get("exp")
        expires_at = datetime.fromtimestamp(exp, tz=timezone.utc).isoformat() if exp else datetime.now(timezone.utc).isoformat()
        
        # Add to blacklist
        blacklisted_token = TokenBlacklist(
            token=token,
            token_type=token_type,
            user_id=user_id,
            expires_at=expires_at,
            reason=reason
        )
        db.add(blacklisted_token)
        await db.commit()
        return True
    
    async def is_token_blacklisted(self, db: AsyncSession, token: str) -> bool:
        """Check if a token is blacklisted."""
        result = await db.execute(
            select(TokenBlacklist).where(TokenBlacklist.token == token)
        )
        return result.scalar_one_or_none() is not None
    
    async def logout_user(self, db: AsyncSession, user_id: int, refresh_token: str):
        """Logout a user by blacklisting their tokens."""
        # Get user's auth data
        result = await db.execute(
            select(Auth).where(Auth.user_id == user_id)
        )
        auth = result.scalar_one_or_none()
        
        if auth and auth.refresh_token:
            # Blacklist the refresh token
            await self.blacklist_token(db, auth.refresh_token, "refresh", user_id, "logout")
            
            # Clear refresh token from auth table
            auth.refresh_token = None
            auth.refresh_token_expires_at = None
            await db.commit()


# Global auth service instance
auth_service = AuthService()
