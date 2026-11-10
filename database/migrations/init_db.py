"""Database schema initialization and initial reference data seeding."""
import logging
from decimal import Decimal
from sqlalchemy import select
from database.base import Base
from database.connection import db_manager
from models.account import AccountType
from config.constants import AccountTypeEnum
from config.settings import settings

logger = logging.getLogger("bms.init_db")


def init_database(engine=None) -> None:
    """Create all tables and seed default account types."""
    eng = engine or db_manager.engine
    logger.info(f"Initializing database schema on dialect: {eng.dialect.name}...")
    Base.metadata.create_all(bind=eng)

    # Seed default account types
    with db_manager.session_scope() as session:
        existing = session.execute(select(AccountType)).scalars().all()
        if not existing:
            logger.info("Seeding default account types...")
            types = [
                AccountType(
                    code=AccountTypeEnum.SAVINGS.value,
                    name="Standard Savings Account",
                    minimum_balance=settings.MIN_ACCOUNT_BALANCE,
                    interest_rate=settings.SAVINGS_INTEREST_RATE,
                    daily_withdrawal_limit=settings.DAILY_WITHDRAWAL_LIMIT,
                ),
                AccountType(
                    code=AccountTypeEnum.CURRENT.value,
                    name="Commercial Current Account",
                    minimum_balance=Decimal("500.00"),
                    interest_rate=Decimal("0.00"),
                    daily_withdrawal_limit=Decimal("100000.00"),
                ),
                AccountType(
                    code=AccountTypeEnum.FIXED_DEPOSIT.value,
                    name="Fixed Term Deposit Account",
                    minimum_balance=Decimal("1000.00"),
                    interest_rate=settings.FIXED_DEPOSIT_INTEREST_RATE,
                    daily_withdrawal_limit=Decimal("0.00"),  # Term-locked
                ),
            ]
            session.add_all(types)
            logger.info("Default account types seeded.")


if __name__ == "__main__":
    init_database()
    print("Database initialization completed successfully.")

