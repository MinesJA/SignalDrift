"""Database utilities for SignalDrift with TimescaleDB support."""

from typing import Optional
from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from sqlalchemy.pool import QueuePool
from src.config import Config

# Create the base class for all models
Base = declarative_base()

class DatabaseManager:
    """Manages database connections and sessions."""
    
    def __init__(self, database_url: Optional[str] = None):
        """Initialize database manager with connection URL."""
        self.database_url = database_url or Config.DATABASE_URL
        self._engine: Optional[Engine] = None
        self._session_factory: Optional[sessionmaker] = None
    
    def get_engine(self) -> Engine:
        """Get or create the database engine."""
        if self._engine is None:
            self._engine = create_engine(
                self.database_url,
                poolclass=QueuePool,
                pool_size=Config.DATABASE_POOL_SIZE,
                max_overflow=Config.DATABASE_MAX_OVERFLOW,
                pool_recycle=3600,  # Recycle connections after 1 hour
                echo=Config.DEBUG  # Echo SQL queries in debug mode
            )
        return self._engine
    
    def get_session_factory(self) -> sessionmaker:
        """Get or create the session factory."""
        if self._session_factory is None:
            self._session_factory = sessionmaker(
                bind=self.get_engine(),
                autocommit=False,
                autoflush=True
            )
        return self._session_factory
    
    def get_session(self) -> Session:
        """Create a new database session."""
        session_factory = self.get_session_factory()
        return session_factory()
    
    def create_tables(self):
        """Create all tables defined in the models."""
        Base.metadata.create_all(self.get_engine())
    
    def drop_tables(self):
        """Drop all tables defined in the models."""
        Base.metadata.drop_all(self.get_engine())

# Global database manager instances
db_manager = DatabaseManager()
test_db_manager = DatabaseManager(Config.DATABASE_TEST_URL)

def get_db_session() -> Session:
    """Get a new database session for the main database."""
    return db_manager.get_session()

def get_test_db_session() -> Session:
    """Get a new database session for the test database."""
    return test_db_manager.get_session()