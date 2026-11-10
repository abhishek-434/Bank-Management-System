"""Financial transaction ledger and account transfer models."""
import uuid
from decimal import Decimal
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Numeric, ForeignKey, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.base import Base
from config.constants import TransactionStatus, TransferStatus


class Transaction(Base):
    """
    Immutable Financial Transaction Ledger.
    Transactions must never be directly modified or deleted.
    """
    __tablename__ = "transactions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    reference_no: Mapped[str] = mapped_column(String(40), unique=True, index=True, nullable=False)
    account_id: Mapped[str] = mapped_column(String(36), ForeignKey("accounts.id", ondelete="RESTRICT"), nullable=False)
    transaction_type: Mapped[str] = mapped_column(String(30), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    previous_balance: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    new_balance: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    description: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    status: Mapped[str] = mapped_column(String(20), default=TransactionStatus.SUCCESS.value, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    account: Mapped["Account"] = relationship("Account", back_populates="transactions")

    __table_args__ = (
        Index("idx_txn_account_date", "account_id", "created_at"),
        Index("idx_txn_type_status", "transaction_type", "status"),
    )

    def __repr__(self) -> str:
        return f"<Transaction {self.reference_no} type={self.transaction_type} amt={self.amount}>"


class Transfer(Base):
    """Internal account-to-account transfer record linking debit and credit."""
    __tablename__ = "transfers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    transfer_reference: Mapped[str] = mapped_column(String(40), unique=True, index=True, nullable=False)
    sender_account_id: Mapped[str] = mapped_column(String(36), ForeignKey("accounts.id"), nullable=False)
    receiver_account_id: Mapped[str] = mapped_column(String(36), ForeignKey("accounts.id"), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    description: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    status: Mapped[str] = mapped_column(String(20), default=TransferStatus.COMPLETED.value, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    sender_account: Mapped["Account"] = relationship("Account", foreign_keys=[sender_account_id], back_populates="sent_transfers")
    receiver_account: Mapped["Account"] = relationship("Account", foreign_keys=[receiver_account_id], back_populates="received_transfers")

    __table_args__ = (
        Index("idx_transfer_sender_receiver", "sender_account_id", "receiver_account_id"),
    )

    def __repr__(self) -> str:
        return f"<Transfer {self.transfer_reference} amt={self.amount} status={self.status}>"

