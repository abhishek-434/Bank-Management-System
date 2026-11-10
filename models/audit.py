"""Audit log entity for compliance and security activity tracking."""
import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Text, ForeignKey, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.base import Base


class AuditLog(Base):
    """Immutable audit trail of critical administrative, financial, and security actions."""
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action: Mapped[str] = mapped_column(String(60), index=True, nullable=False)
    target_entity: Mapped[str] = mapped_column(String(50), nullable=False)
    target_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    details: Mapped[str] = mapped_column(Text, default="", nullable=False)
    ip_address: Mapped[str] = mapped_column(String(45), default="127.0.0.1", nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        index=True,
        nullable=False,
    )

    # Relationships
    user: Mapped[Optional["User"]] = relationship("User", back_populates="audit_logs")

    __table_args__ = (
        Index("idx_audit_action_time", "action", "timestamp"),
    )

    def __repr__(self) -> str:
        return f"<AuditLog {self.action} on {self.target_entity} at {self.timestamp}>"

