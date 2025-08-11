"""Verification token model for OTP flows (email verification, password reset, etc.)."""

from enum import Enum
from sqlalchemy import String, Enum as SQLEnum, Boolean, Index
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin


class VerificationType(str, Enum):
    """Types of verification supported by the system."""

    VERIFY_EMAIL = "verify_email"
    FORGOT_PASSWORD = "forgot_password"


class VerificationToken(Base, TimestampMixin):
    """Stores 6-digit OTP tokens tied to an email and purpose/type."""

    __tablename__ = "verification_tokens"

    type: Mapped[VerificationType] = mapped_column(
        SQLEnum(VerificationType, name="verification_type"),
        nullable=False,
        index=True,
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    token: Mapped[str] = mapped_column(String(6), nullable=False, index=True)
    used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    expires_at: Mapped[str] = mapped_column(String(50), nullable=False)  # ISO datetime string

    __table_args__ = (
        Index("ix_verif_email_type_created", "email", "type", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<VerificationToken(id={self.id}, email='{self.email}', type='{self.type}')>"
