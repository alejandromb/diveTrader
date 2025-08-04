#!/usr/bin/env python3
"""
Database migration script for DiveTrader
Ensures all tables are created and up to date
"""

import sys
import os

# Add the backend directory to Python path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker
from database.database import DATABASE_URL, engine
from database.models import Base, Strategy
from services.strategy_settings_service import strategy_settings_service
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_table_exists(engine, table_name: str) -> bool:
    """Check if a table exists in the database"""
    inspector = inspect(engine)
    return table_name in inspector.get_table_names()

def migrate_database():
    """Run database migrations"""
    logger.info("Starting database migration...")
    
    try:
        # Create all tables (this is idempotent - won't recreate existing tables)
        logger.info("Creating/updating database tables...")
        Base.metadata.create_all(bind=engine)
        
        # Check if strategy_settings table was created
        if check_table_exists(engine, "strategy_settings"):
            logger.info("✅ strategy_settings table is present")
        else:
            logger.error("❌ strategy_settings table was not created")
            return False
        
        # Initialize default settings for existing strategies
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        try:
            # Get all existing strategies
            strategies = db.query(Strategy).all()
            logger.info(f"Found {len(strategies)} existing strategies")
            
            for strategy in strategies:
                # Check if strategy already has settings
                existing_settings = strategy_settings_service.get_all_settings(db, strategy.id)
                
                if not existing_settings:
                    # Initialize default settings
                    logger.info(f"Initializing settings for strategy {strategy.id} ({strategy.strategy_type.value})")
                    success = strategy_settings_service.initialize_default_settings(
                        db, strategy.id, strategy.strategy_type.value
                    )
                    if success:
                        logger.info(f"✅ Settings initialized for strategy {strategy.id}")
                    else:
                        logger.warning(f"⚠️  Failed to initialize settings for strategy {strategy.id}")
                else:
                    logger.info(f"✅ Strategy {strategy.id} already has {len(existing_settings)} settings")
        
        except Exception as e:
            logger.error(f"Error initializing settings for existing strategies: {e}")
            db.rollback()
        finally:
            db.close()
        
        logger.info("✅ Database migration completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Database migration failed: {e}")
        return False

def verify_migration():
    """Verify that the migration was successful"""
    logger.info("Verifying database migration...")
    
    try:
        # Check that all expected tables exist
        expected_tables = [
            "strategies", 
            "positions", 
            "trades", 
            "performance_metrics", 
            "portfolios", 
            "strategy_event_logs",
            "strategy_settings"  # New table
        ]
        
        missing_tables = []
        for table in expected_tables:
            if check_table_exists(engine, table):
                logger.info(f"✅ Table '{table}' exists")
            else:
                logger.error(f"❌ Table '{table}' is missing")
                missing_tables.append(table)
        
        if missing_tables:
            logger.error(f"❌ Migration verification failed. Missing tables: {missing_tables}")
            return False
        
        logger.info("✅ Database migration verification passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Migration verification failed: {e}")
        return False

if __name__ == "__main__":
    logger.info(f"Using database: {DATABASE_URL}")
    
    # Run migration
    migration_success = migrate_database()
    
    if migration_success:
        # Verify migration
        verification_success = verify_migration()
        
        if verification_success:
            logger.info("🎉 Database is ready!")
            sys.exit(0)
        else:
            logger.error("💥 Migration verification failed")
            sys.exit(1)
    else:
        logger.error("💥 Database migration failed")
        sys.exit(1)