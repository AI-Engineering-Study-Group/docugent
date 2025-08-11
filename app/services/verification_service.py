"""Service for generating, storing, sending, and verifying OTP tokens."""

import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, update

from app.config.settings import settings
from app.models import VerificationToken, VerificationType, User
from app.services.email_service import email_service


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class VerificationService:
    def __init__(self) -> None:
        self.otp_length = 6
        self.expire_minutes = settings.otp_expire_minutes

    def _generate_token(self) -> str:
        # 6-digit numeric, zero-padded
        return f"{secrets.randbelow(10**self.otp_length):0{self.otp_length}d}"

    async def create_and_send(self, db: AsyncSession, email: str, vtype: VerificationType) -> Tuple[str, str]:
        token = self._generate_token()
        expires_at_dt = datetime.now(timezone.utc) + timedelta(minutes=self.expire_minutes)
        vt = VerificationToken(
            type=vtype,
            email=email.lower(),
            token=token,
            expires_at=expires_at_dt.isoformat(),
        )
        db.add(vt)
        await db.commit()

        subject = "Verify your email" if vtype == VerificationType.VERIFY_EMAIL else "Password reset code"
        body = (
            f"Your verification code is {token}. It expires in {self.expire_minutes} minutes."
        )
        html = (
            f"<p>Your verification code is <strong>{token}</strong>.</p>"
            f"<p>This code expires in {self.expire_minutes} minutes.</p>"
        )
        email_service.send_email(email, subject, body, html)
        return token, vt.expires_at

    async def resend(self, db: AsyncSession, email: str, vtype: VerificationType) -> Tuple[str, str]:
        # Optional: mark previous unused tokens as used to avoid confusion
        await db.execute(
            update(VerificationToken)
            .where(and_(VerificationToken.email == email.lower(), VerificationToken.type == vtype, VerificationToken.used == False))
            .values(used=True)
        )
        await db.commit()
        return await self.create_and_send(db, email, vtype)

    async def verify(self, db: AsyncSession, email: str, vtype: VerificationType, token: str) -> bool:
        # Fetch the latest matching unused token
        result = await db.execute(
            select(VerificationToken)
            .where(
                and_(
                    VerificationToken.email == email.lower(),
                    VerificationToken.type == vtype,
                    VerificationToken.token == token,
                    VerificationToken.used == False,
                )
            )
            .order_by(VerificationToken.created_at.desc())
        )
        vt = result.scalar_one_or_none()
        if not vt:
            return False
        # Check expiry
        try:
            if datetime.fromisoformat(vt.expires_at) < datetime.now(timezone.utc):
                return False
        except Exception:
            return False
        # Mark used
        vt.used = True
        await db.commit()

        # Side-effects for certain types
        if vtype == VerificationType.VERIFY_EMAIL:
            # Mark user verified if exists
            user_res = await db.execute(select(User).where(User.email == email.lower()))
            user = user_res.scalar_one_or_none()
            if user and not user.is_verified:
                user.is_verified = True
                await db.commit()
        return True


verification_service = VerificationService()
