"""User model for public user information."""

from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .role import Role
    from .auth import Auth


class User(Base, TimestampMixin):
    """User model containing public user information."""
    
    __tablename__ = "users"
    
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Foreign Key to Role (Many users to One role)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"), nullable=False)
    
    # Relationships
    role: Mapped["Role"] = relationship(
        "Role",
        back_populates="users",
        lazy="selectin",
    )
    # One-to-one child Auth; deleting a user deletes its auth via DB FK cascade
    auth: Mapped["Auth"] = relationship(
        "Auth",
        back_populates="user",
        uselist=False,
        passive_deletes=True,
    lazy="selectin",
    )
    
    @property
    def full_name(self) -> str:
        """Get user's full name."""
        return f"{self.first_name} {self.last_name}"
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}', name='{self.full_name}')>"
