"""Customer profile model."""
import uuid
from datetime import date, datetime, timezone
from typing import Optional, List
from sqlalchemy import String, Date, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.base import Base, TimestampMixin
from config.constants import CustomerStatus


class Customer(Base, TimestampMixin):
    __tablename__ = "customers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    customer_code: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    first_name: Mapped[str] = mapped_column(String(60), nullable=False)
    last_name: Mapped[str] = mapped_column(String(60), nullable=False)
    date_of_birth: Mapped[date] = mapped_column(Date, nullable=False)
    email: Mapped[str] = mapped_column(String(120), unique=True, index=True, nullable=False)
    phone: Mapped[str] = mapped_column(String(25), nullable=False)
    address: Mapped[str] = mapped_column(String(255), nullable=False)
    govt_id_masked: Mapped[str] = mapped_column(String(50), nullable=False)  # Synthetic masked reference
    status: Mapped[str] = mapped_column(String(20), default=CustomerStatus.ACTIVE.value, nullable=False)

    # Relationships
    user: Mapped[Optional["User"]] = relationship("User", back_populates="customer")
    accounts: Mapped[List["Account"]] = relationship("Account", back_populates="customer", cascade="all, delete-orphan")
    loans: Mapped[List["Loan"]] = relationship("Loan", back_populates="customer")

    __table_args__ = (
        Index("idx_customer_name", "first_name", "last_name"),
    )

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def __repr__(self) -> str:
        return f"<Customer {self.customer_code} - {self.full_name}>"

