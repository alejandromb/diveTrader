"""
SQLModel-based database connection and session management
Replaces the old SQLAlchemy setup with SQLModel for better type safety
"""

from sqlmodel import create_engine, SQLModel, Session
from typing import Generator
import os
from dotenv import load_dotenv

load_dotenv()

# Database URL - defaults to PostgreSQL for AWS compatibility
# For local development, can use SQLite if PostgreSQL not available
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/divetrader")

# For local development fallback to SQLite
postgres_available = os.getenv("POSTGRES_AVAILABLE", "false").lower() == "true"
if "postgresql" in DATABASE_URL and not postgres_available:
    DATABASE_URL = "sqlite:///./divetrader_sqlmodel.db"

# Create engine with SQLModel
engine = create_engine(
    DATABASE_URL,
    # SQLite specific settings
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    echo=False  # Set to True for SQL query logging
)

def create_tables():
    """Create all database tables"""
    # Import all models to ensure they're registered
    from database.sqlmodel_models import (
        Strategy, Position, Trade, PerformanceMetric, Portfolio,
        StrategyEventLog, BTCScalpingSettings, PortfolioDistributorSettings,
        LegacyStrategySetting
    )
    
    SQLModel.metadata.create_all(engine)

def get_session() -> Generator[Session, None, None]:
    """Dependency for getting database sessions"""
    with Session(engine) as session:
        yield session

# Legacy compatibility - some code still uses SessionLocal
def SessionLocal():
    """Legacy compatibility for old SQLAlchemy session pattern"""
    return Session(engine)

# Dependency for FastAPI
def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for database sessions"""
    return get_session()

# Initialize database on import
def init_database():
    """Initialize database with all tables"""
    create_tables()
    print(f"✅ SQLModel database initialized at: {DATABASE_URL}")

if __name__ == "__main__":
    init_database()