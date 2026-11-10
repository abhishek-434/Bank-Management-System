"""Loan management and repayment tracking models."""
import uuid
from decimal import Decimal
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import String, Numeric, Integer, ForeignKey, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.base import Base, TimestampMixin
from config.constants import LoanStatus


class Loan(Base, TimestampMixin):
    """Educational demonstration loan model."""
    __tablename__ = "loans"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    loan_reference: Mapped[str] = mapped_column(String(30), unique=True, index=True, nullable=False)
    customer_id: Mapped[str] = mapped_column(String(36), ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False)
    principal_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    interest_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)  # Annual interest rate %
    duration_months: Mapped[int] = mapped_column(Integer, nullable=False)
    total_payable: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    outstanding_balance: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default=LoanStatus.APPLIED.value, nullable=False)
    applied_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    customer: Mapped["Customer"] = relationship("Customer", back_populates="loans")
    repayments: Mapped[List["LoanRepayment"]] = relationship("LoanRepayment", back_populates="loan", order_by="LoanRepayment.paid_at")

    __table_args__ = (
        Index("idx_loan_customer_status", "customer_id", "status"),
    )

    def __repr__(self) -> str:
        return f"<Loan {self.loan_reference} principal={self.principal_amount} balance={self.outstanding_balance} status={self.status}>"


class LoanRepayment(Base):
    """Repayment record towards an approved active loan."""
    __tablename__ = "loan_repayments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    loan_id: Mapped[str] = mapped_column(String(36), ForeignKey("loans.id", ondelete="CASCADE"), nullable=False)
    payment_reference: Mapped[str] = mapped_column(String(40), unique=True, index=True, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    principal_portion: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    interest_portion: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    balance_after_payment: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    paid_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    loan: Mapped["Loan"] = relationship("Loan", back_populates="repayments")

    def __repr__(self) -> str:
        return f"<LoanRepayment {self.payment_reference} amt={self.amount} rem={self.balance_after_payment}>"

