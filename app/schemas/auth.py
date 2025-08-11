"""Authentication and authorization schemas."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, field_validator

from .base import SuccessResponseSchema
from app.models.verification_token import VerificationType


# Authentication Schemas
class UserRegistrationRequest(BaseModel):
    """User registration request schema."""
    email: EmailStr
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters")
    first_name: str = Field(..., max_length=100)
    last_name: str = Field(..., max_length=100)
    phone_number: Optional[str] = Field(None, max_length=20)
    role_id: Optional[int] = Field(1, description="Default role ID (user)")
    
    @field_validator('password')
    def validate_password(cls, v):
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v


class UserLoginRequest(BaseModel):
    """User login request schema."""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Token response schema."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds
    user: "UserResponse"


class RefreshTokenRequest(BaseModel):
    """Refresh token request schema."""
    refresh_token: str


class LogoutRequest(BaseModel):
    """Logout request schema."""
    refresh_token: str


# User Schemas
class UserResponse(BaseModel):
    """User response schema - only public data."""
    id: int
    email: str
    first_name: str
    last_name: str
    full_name: str
    phone_number: Optional[str]
    is_active: bool
    is_verified: bool
    role: "RoleResponse"
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class UserUpdateRequest(BaseModel):
    """User update request schema."""
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    phone_number: Optional[str] = Field(None, max_length=20)


class ChangePasswordRequest(BaseModel):
    """Change password request schema."""
    current_password: str
    new_password: str = Field(..., min_length=8)
    
    @field_validator('new_password')
    def validate_new_password(cls, v):
        """Validate new password strength."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v


# Role Schemas
class RoleResponse(BaseModel):
    """Role response schema."""
    id: int
    name: str
    description: Optional[str]
    permissions: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class RoleCreateRequest(BaseModel):
    """Role creation request schema."""
    name: str = Field(..., max_length=50)
    description: Optional[str] = None
    permissions: Optional[str] = None  # JSON string
    is_active: bool = True


class RoleUpdateRequest(BaseModel):
    """Role update request schema."""
    name: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    permissions: Optional[str] = None  # JSON string
    is_active: Optional[bool] = None


# Response Schemas
class AuthSuccessResponse(SuccessResponseSchema[TokenResponse]):
    """Authentication success response."""
    pass


class UserSuccessResponse(SuccessResponseSchema[UserResponse]):
    """User success response."""
    pass


class UsersListResponse(SuccessResponseSchema[List[UserResponse]]):
    """Users list response."""
    pass


class RoleSuccessResponse(SuccessResponseSchema[RoleResponse]):
    """Role success response."""
    pass


class RolesListResponse(SuccessResponseSchema[List[RoleResponse]]):
    """Roles list response."""
    pass


# Verification Schemas
class VerificationCreateRequest(BaseModel):
    email: EmailStr
    type: VerificationType = Field(VerificationType.VERIFY_EMAIL)


class VerificationVerifyRequest(BaseModel):
    email: EmailStr
    type: VerificationType
    token: str = Field(..., min_length=6, max_length=6)


class VerificationResendRequest(BaseModel):
    email: EmailStr
    type: VerificationType


class VerificationCreateResponse(BaseModel):
    email: EmailStr
    type: VerificationType
    expires_at: datetime


class VerificationSuccessResponse(SuccessResponseSchema[VerificationCreateResponse]):
    pass


# Update forward references
UserResponse.model_rebuild()
TokenResponse.model_rebuild()
