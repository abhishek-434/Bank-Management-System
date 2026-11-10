"""Database connection engine and session lifecycle management."""
import logging
from contextlib import contextmanager
from typing import Generator
from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import OperationalError
from config.settings import settings
import models  # Ensure all models are registered

logger = logging.getLogger("bms.database")
logging.basicConfig(level=logging.INFO)


class DatabaseManager:
    """Manages database engine creation, fallback capabilities, and sessions."""

    def __init__(self):
        self._engine: Engine | None = None
        self._session_factory: sessionmaker | None = None
        self._active_dialect: str = ""

    def initialize(self, custom_uri: str = None) -> Engine:
        """Initialize the database engine."""
        if custom_uri:
            self._engine = create_engine(custom_uri, echo=False)
            self._active_dialect = self._engine.dialect.name
            self._session_factory = sessionmaker(
            bind=self._engine,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
        )
            return self._engine

        if settings.DB_ENGINE == "postgresql":
            pg_uri = settings.get_postgres_uri()
            try:
                logger.info(f"Connecting to PostgreSQL at {settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}...")
                test_engine = create_engine(
                    pg_uri,
                    pool_size=settings.DB_POOL_SIZE,
                    max_overflow=settings.DB_MAX_OVERFLOW,
                    pool_pre_ping=True,
                    echo=False,
                    connect_args={"connect_timeout": 1},
                )
                # Verify actual connectivity
                with test_engine.connect() as conn:
                    pass
                self._engine = test_engine
                self._active_dialect = "postgresql"
                logger.info("Successfully connected to PostgreSQL.")
            except (OperationalError, Exception) as exc:
                logger.warning(
                    f"PostgreSQL connection failed ({exc}). "
                    f"Falling back to local SQLite persistent database at '{settings.DB_SQLITE_PATH}'."
                )
                sqlite_uri = settings.get_sqlite_uri()
                sqlite_file = settings.BASE_DIR / settings.DB_SQLITE_PATH
                try:
                    sqlite_file.touch(exist_ok=True)
                except OSError:
                    pass
                self._engine = create_engine(
                    sqlite_uri,
                    connect_args={"check_same_thread": False},
                    echo=False,
                )
                self._active_dialect = "sqlite"
        else:
            sqlite_uri = settings.get_sqlite_uri()
            sqlite_file = settings.BASE_DIR / settings.DB_SQLITE_PATH
            try:
                sqlite_file.touch(exist_ok=True)
            except OSError:
                pass
            logger.info(f"Connecting to SQLite database at {settings.DB_SQLITE_PATH}...")
            self._engine = create_engine(
                sqlite_uri,
                connect_args={"check_same_thread": False},
                echo=False,
            )
            self._active_dialect = "sqlite"

        self._session_factory = sessionmaker(
            bind=self._engine,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
        )
        return self._engine

    @property
    def engine(self) -> Engine:
        if self._engine is None:
            self.initialize()
        return self._engine

    @property
    def active_dialect(self) -> str:
        if self._engine is None:
            self.initialize()
        return self._active_dialect

    @property
    def session_factory(self) -> sessionmaker:
        if self._session_factory is None:
            self.initialize()
        return self._session_factory

    def get_session(self) -> Session:
        """Create a new database session."""
        return self.session_factory()

    @contextmanager
    def session_scope(self) -> Generator[Session, None, None]:
        """Provide a transactional scope around a series of operations."""
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()


db_manager = DatabaseManager()


def get_db_session() -> Generator[Session, None, None]:
    """Convenience context manager for database operations."""
    return db_manager.session_scope()
