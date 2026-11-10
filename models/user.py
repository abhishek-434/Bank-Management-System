"""User model for authentication, authorization, and session tracking."""
import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Boolean, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.base import Base, TimestampMixin
from config.constants import UserRole


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), default=UserRole.CUSTOMER.value, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    locked_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    customer: Mapped[Optional["Customer"]] = relationship("Customer", back_populates="user", uselist=False)
    employee: Mapped[Optional["Employee"]] = relationship("Employee", back_populates="user", uselist=False)
    audit_logs: Mapped[list["AuditLog"]] = relationship("AuditLog", back_populates="user")

    def is_locked(self) -> bool:
        """Check if account is currently locked due to excessive failed attempts."""
        if not self.locked_until:
            return False
        # Normalize timezone
        now = datetime.now(timezone.utc)
        if self.locked_until.tzinfo is None:
            return self.locked_until > datetime.utcnow()
        return self.locked_until > now

    def __repr__(self) -> str:
        return f"<User username={self.username} role={self.role} active={self.is_active}>"

