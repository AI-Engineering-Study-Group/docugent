"""Auth model for sensitive user authentication data."""

from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .user import User


class Auth(Base, TimestampMixin):
    """Auth model containing sensitive authentication information."""
    
    __tablename__ = "auth"
    
    # One-to-One relationship with User
    # Ensure DB-level cascade delete from users -> auth
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    
    # Authentication fields
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    salt: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Token management
    refresh_token: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    refresh_token_expires_at: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # ISO datetime string
    
    # Password reset
    reset_token: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    reset_token_expires_at: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # ISO datetime string
    
    # Security fields
    failed_login_attempts: Mapped[int] = mapped_column(default=0, nullable=False)
    locked_until: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # ISO datetime string
    last_login_at: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # ISO datetime string
    
    # Relationships
    # passive_deletes allows the database ON DELETE CASCADE to handle child deletion
    user: Mapped["User"] = relationship("User", back_populates="auth", passive_deletes=True)
    
    def __repr__(self) -> str:
        return f"<Auth(id={self.id}, user_id={self.user_id})>"
