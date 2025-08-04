from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os
from dotenv import load_dotenv

load_dotenv()

# Database URL - defaults to PostgreSQL for AWS compatibility
# For local development, can use SQLite if PostgreSQL not available
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/divetrader")

# For local development fallback to SQLite
postgres_available = os.getenv("POSTGRES_AVAILABLE", "false").lower() == "true"
if "postgresql" in DATABASE_URL and not postgres_available:
    DATABASE_URL = "sqlite:///./divetrader.db"

engine = create_engine(
    DATABASE_URL,
    # SQLite specific settings
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency for FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Create tables
def create_tables():
    from .models import Base
    Base.metadata.create_all(bind=engine)