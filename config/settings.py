"""Application settings and configuration loader."""
import os
from decimal import Decimal
from pathlib import Path
from dotenv import load_dotenv

# Base directory of the BMS project
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env file
ENV_PATH = BASE_DIR / ".env"
load_dotenv(dotenv_path=ENV_PATH)


class Settings:
    """Central configuration class for BMS."""

    def __init__(self):
        self.BASE_DIR: Path = BASE_DIR
        self.EXPORTS_DIR: Path = BASE_DIR / "exports"
        self.RECEIPTS_DIR: Path = BASE_DIR / "receipts"
        self.STATEMENTS_DIR: Path = BASE_DIR / "statements"

        # Ensure directories exist
        for directory in [self.EXPORTS_DIR, self.RECEIPTS_DIR, self.STATEMENTS_DIR]:
            try:
                directory.mkdir(parents=True, exist_ok=True)
            except OSError:
                pass

        # Database
        self.DB_ENGINE: str = os.getenv("DB_ENGINE", "postgresql").lower()
        self.DB_HOST: str = os.getenv("DB_HOST", "localhost")
        self.DB_PORT: int = int(os.getenv("DB_PORT", "5432"))
        self.DB_NAME: str = os.getenv("DB_NAME", "bms_db")
        self.DB_USER: str = os.getenv("DB_USER", "postgres")
        self.DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
        self.DB_POOL_SIZE: int = int(os.getenv("DB_POOL_SIZE", "10"))
        self.DB_MAX_OVERFLOW: int = int(os.getenv("DB_MAX_OVERFLOW", "20"))
        self.DB_SQLITE_PATH: str = os.getenv("DB_SQLITE_PATH", str(BASE_DIR / "bms.db"))

        # Testing DB
        self.TEST_DB_ENGINE: str = os.getenv("TEST_DB_ENGINE", "sqlite")
        self.TEST_DB_NAME: str = os.getenv("TEST_DB_NAME", ":memory:")

        # Security
        self.APP_SECRET_KEY: str = os.getenv("APP_SECRET_KEY", "bms-default-demo-secret-key-32chars-min")
        self.SESSION_TIMEOUT_MINUTES: int = int(os.getenv("SESSION_TIMEOUT_MINUTES", "30"))
        self.MAX_LOGIN_ATTEMPTS: int = int(os.getenv("MAX_LOGIN_ATTEMPTS", "5"))
        self.ACCOUNT_LOCK_MINUTES: int = int(os.getenv("ACCOUNT_LOCK_MINUTES", "15"))
        self.BCRYPT_ROUNDS: int = int(os.getenv("BCRYPT_ROUNDS", "12"))

        # Financial Business Rules
        self.DAILY_WITHDRAWAL_LIMIT: Decimal = Decimal(os.getenv("DAILY_WITHDRAWAL_LIMIT", "50000.00"))
        self.MIN_ACCOUNT_BALANCE: Decimal = Decimal(os.getenv("MIN_ACCOUNT_BALANCE", "100.00"))
        self.SAVINGS_INTEREST_RATE: Decimal = Decimal(os.getenv("SAVINGS_INTEREST_RATE", "3.50"))
        self.FIXED_DEPOSIT_INTEREST_RATE: Decimal = Decimal(os.getenv("FIXED_DEPOSIT_INTEREST_RATE", "6.50"))
        self.FIXED_DEPOSIT_MIN_TERM_DAYS: int = int(os.getenv("FIXED_DEPOSIT_MIN_TERM_DAYS", "30"))

        # UI Settings
        self.UI_APPEARANCE_MODE: str = os.getenv("UI_APPEARANCE_MODE", "Dark")
        self.UI_COLOR_THEME: str = os.getenv("UI_COLOR_THEME", "blue")
        self.WINDOW_DEFAULT_WIDTH: int = int(os.getenv("WINDOW_DEFAULT_WIDTH", "1366"))
        self.WINDOW_DEFAULT_HEIGHT: int = int(os.getenv("WINDOW_DEFAULT_HEIGHT", "850"))

    def get_postgres_uri(self) -> str:
        """Construct PostgreSQL connection URL for SQLAlchemy."""
        return (
            f"postgresql+psycopg2://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    def get_sqlite_uri(self, path: str = None) -> str:
        """Construct SQLite connection URL for SQLAlchemy with absolute path."""
        raw_path = path or self.DB_SQLITE_PATH
        abs_path = (self.BASE_DIR / raw_path).resolve().as_posix()
        return f"sqlite:///{abs_path}"


settings = Settings()
