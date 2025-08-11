"""Authentication API routes."""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import User, Auth, Role
from app.schemas.auth import (
    UserRegistrationRequest,
    UserLoginRequest,
    TokenResponse,
    RefreshTokenRequest,
    LogoutRequest,
    AuthSuccessResponse,
    UserSuccessResponse,
    ChangePasswordRequest,
#     VerificationVerifyRequest,
#     VerificationResendRequest,
#     VerificationCreateResponse,
#     VerificationSuccessResponse,
)
from app.schemas.base import SuccessResponseSchema
from app.services.auth_service import auth_service
from app.dependencies.auth import get_current_active_user
from app.services.verification_service import verification_service
from app.models import VerificationType


router = APIRouter()


@router.post("/register", response_model=AuthSuccessResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserRegistrationRequest,
    db: AsyncSession = Depends(get_db)
):
    """Register a new user."""
    # Check if user already exists
    result = await db.execute(select(User).where(User.email == user_data.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check if role exists
    result = await db.execute(select(Role).where(Role.id == user_data.role_id, Role.is_active == True))
    role = result.scalar_one_or_none()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid role specified"
        )
    
    # Hash password
    hashed_password, salt = auth_service.hash_password(user_data.password)
    
    # Create user
    user = User(
        email=user_data.email,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        phone_number=user_data.phone_number,
        role_id=user_data.role_id,
        is_active=True,
        is_verified=False
    )
    db.add(user)
    await db.flush()  # Get user ID
    
    # Create auth record
    auth = Auth(
        user_id=user.id,
        hashed_password=hashed_password,
        salt=salt
    )
    db.add(auth)
    await db.commit()
    
    # Refresh user to get relationships
    await db.refresh(user)
    
    # Create tokens
    access_token, refresh_token, expires_at = await auth_service.create_tokens_for_user(db, user)
    
    token_response = TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=auth_service.access_token_expire_minutes * 60,
        user=user
    )
    
    # Send verification code
    # try:
    #     await verification_service.create_and_send(db, user.email, VerificationType.VERIFY_EMAIL)
    # except Exception:
    #     # Don't fail registration on email errors; logs already captured
    #     pass

    return SuccessResponseSchema(
        data=token_response,
        message="User registered successfully."
    )


@router.post("/login", response_model=AuthSuccessResponse)
async def login_user(
    login_data: UserLoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """Login a user."""
    # Authenticate user
    user = await auth_service.authenticate_user(db, login_data.email, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Create tokens
    access_token, refresh_token, expires_at = await auth_service.create_tokens_for_user(db, user)
    
    token_response = TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=auth_service.access_token_expire_minutes * 60,
        user=user
    )
    
    return SuccessResponseSchema(
        data=token_response,
        message="Login successful"
    )


@router.post("/refresh", response_model=AuthSuccessResponse)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
):
    """Refresh an access token."""
    result = await auth_service.refresh_access_token(db, refresh_data.refresh_token)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    access_token, refresh_token, expires_at = result
    
    # Get user for response
    payload = auth_service.verify_token(access_token, "access")
    user_id = payload.get("user_id")
    
    result = await db.execute(
        select(User).options(selectinload(User.role), selectinload(User.auth)).where(User.id == user_id)
    )
    user = result.scalar_one()
    
    token_response = TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=auth_service.access_token_expire_minutes * 60,
        user=user
    )
    
    return SuccessResponseSchema(
        data=token_response,
        message="Token refreshed successfully"
    )


@router.post("/logout")
async def logout_user(
    logout_data: LogoutRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Logout a user."""
    await auth_service.logout_user(db, current_user.id, logout_data.refresh_token)
    
    return SuccessResponseSchema(
        data=None,
        message="Logout successful"
    )


@router.get("/me", response_model=UserSuccessResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """Get current user information."""
    return SuccessResponseSchema(
        data=current_user,
        message="User information retrieved successfully"
    )


@router.post("/change-password")
async def change_password(
    password_data: ChangePasswordRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Change user password."""
    # Verify current password
    if not auth_service.verify_password(
        password_data.current_password,
        current_user.auth.hashed_password,
        current_user.auth.salt or ""
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Hash new password
    new_hashed_password, new_salt = auth_service.hash_password(password_data.new_password)
    
    # Update password
    current_user.auth.hashed_password = new_hashed_password
    current_user.auth.salt = new_salt
    
    # Invalidate existing refresh token
    if current_user.auth.refresh_token:
        await auth_service.blacklist_token(
            db, current_user.auth.refresh_token, "refresh", current_user.id, "password_change"
        )
        current_user.auth.refresh_token = None
        current_user.auth.refresh_token_expires_at = None
    
    await db.commit()
    
    return SuccessResponseSchema(
        data=None,
        message="Password changed successfully. Please login again."
    )


# def _dispatch_target_service(vtype: VerificationType):
#     """Switch-like dispatcher for different verification flows."""
#     match vtype:
#         case VerificationType.VERIFY_EMAIL:
#             return verification_service
#         case VerificationType.FORGOT_PASSWORD:
#             return verification_service
#         case _:
#             return verification_service


# @router.post("/verify", response_model=VerificationSuccessResponse)
# async def verify_token(
#     payload: VerificationVerifyRequest,
#     db: AsyncSession = Depends(get_db),
# ):
#     svc = _dispatch_target_service(payload.type)
#     ok = await svc.verify(db, payload.email, payload.type, payload.token)
#     if not ok:
#         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired token")
#     resp = VerificationCreateResponse(
#         email=payload.email,
#         type=payload.type,
#         expires_at=datetime.utcnow(),
#     )
#     return SuccessResponseSchema(data=resp, message="Verification successful")


# @router.post("/resend-otp", response_model=VerificationSuccessResponse)
# async def resend_otp(
#     payload: VerificationResendRequest,
#     db: AsyncSession = Depends(get_db),
# ):
#     svc = _dispatch_target_service(payload.type)
#     _, expires_at = await svc.resend(db, payload.email, payload.type)
#     resp = VerificationCreateResponse(
#         email=payload.email,
#         type=payload.type,
#         expires_at=datetime.fromisoformat(expires_at),
#     )
#     return SuccessResponseSchema(data=resp, message="OTP resent")
