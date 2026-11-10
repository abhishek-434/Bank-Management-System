"""Bank account types and customer bank account models."""
import uuid
from decimal import Decimal
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import String, Numeric, Integer, ForeignKey, DateTime, CheckConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.base import Base, TimestampMixin
from config.constants import AccountStatus, AccountTypeEnum


class AccountType(Base):
    __tablename__ = "account_types"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(60), nullable=False)
    minimum_balance: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("100.00"), nullable=False)
    interest_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0.00"), nullable=False)
    daily_withdrawal_limit: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("50000.00"), nullable=False)

    # Relationships
    accounts: Mapped[List["Account"]] = relationship("Account", back_populates="account_type")

    def __repr__(self) -> str:
        return f"<AccountType {self.code} min_bal={self.minimum_balance}>"


class Account(Base, TimestampMixin):
    __tablename__ = "accounts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    account_number: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    customer_id: Mapped[str] = mapped_column(String(36), ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False)
    account_type_id: Mapped[int] = mapped_column(Integer, ForeignKey("account_types.id"), nullable=False)
    current_balance: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    status: Mapped[str] = mapped_column(String(20), default=AccountStatus.ACTIVE.value, nullable=False)
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    customer: Mapped["Customer"] = relationship("Customer", back_populates="accounts")
    account_type: Mapped["AccountType"] = relationship("AccountType", back_populates="accounts")
    transactions: Mapped[List["Transaction"]] = relationship("Transaction", back_populates="account", order_by="desc(Transaction.created_at)")
    sent_transfers: Mapped[List["Transfer"]] = relationship("Transfer", foreign_keys="Transfer.sender_account_id", back_populates="sender_account")
    received_transfers: Mapped[List["Transfer"]] = relationship("Transfer", foreign_keys="Transfer.receiver_account_id", back_populates="receiver_account")

    __table_args__ = (
        CheckConstraint("current_balance >= 0.00", name="chk_non_negative_balance"),
        Index("idx_account_cust_status", "customer_id", "status"),
    )

    def is_operational(self) -> bool:
        """Check if account is active and eligible for transactions."""
        return self.status == AccountStatus.ACTIVE.value

    def __repr__(self) -> str:
        return f"<Account num={self.account_number} bal={self.current_balance} status={self.status}>"

