"""Token blacklist model for managing revoked tokens."""

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin


class TokenBlacklist(Base, TimestampMixin):
    """Model for storing blacklisted/revoked tokens."""
    
    __tablename__ = "token_blacklist"
    
    token: Mapped[str] = mapped_column(Text, unique=True, nullable=False, index=True)
    token_type: Mapped[str] = mapped_column(String(20), nullable=False)  # 'access' or 'refresh'
    user_id: Mapped[int] = mapped_column(nullable=False, index=True)
    expires_at: Mapped[str] = mapped_column(String(50), nullable=False)  # ISO datetime string
    reason: Mapped[str] = mapped_column(String(100), default="logout", nullable=False)
    
    def __repr__(self) -> str:
        return f"<TokenBlacklist(id={self.id}, token_type='{self.token_type}', user_id={self.user_id})>"
