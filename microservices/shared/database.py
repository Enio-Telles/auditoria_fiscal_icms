"""
Database configuration and connection management for microservices
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


class DatabaseConfig:
    """Database configuration for multi-tenant architecture"""

    def __init__(self):
        self.DATABASE_URL = os.getenv(
            "DATABASE_URL",
            "sqlite:///./auditoria_fiscal_icms.db",  # Default to SQLite for development
        )
        self.engine = None
        self.SessionLocal = None

    def initialize(self):
        """Initialize database connection"""
        # Special handling for SQLite
        if self.DATABASE_URL.startswith("sqlite"):
            self.engine = create_engine(
                self.DATABASE_URL,
                connect_args={"check_same_thread": False},  # SQLite specific
            )
        else:
            self.engine = create_engine(self.DATABASE_URL)

        self.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )
        return self.engine

    def get_session(self):
        """Get database session"""
        if not self.SessionLocal:
            self.initialize()
        return self.SessionLocal()

    def get_tenant_schema(self, tenant_id: str) -> str:
        """Get schema name for tenant"""
        return f"tenant_{tenant_id}"


# Global database configuration
db_config = DatabaseConfig()


def get_db():
    """Dependency for FastAPI"""
    session = db_config.get_session()
    try:
        yield session
    finally:
        session.close()
