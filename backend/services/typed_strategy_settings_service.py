"""
Typed Strategy Settings Service using SQLModel
Provides type-safe CRUD operations for strategy settings
"""

from typing import Dict, Any, Optional, Union, Type
from sqlalchemy.orm import Session
from sqlmodel import select
from database.strategy_settings_models import (
    BTCScalpingSettings,
    PortfolioDistributorSettings,
    StrategySettingsFactory,
    StrategyTypeEnum
)
from database.models import Strategy
import logging

logger = logging.getLogger(__name__)

class TypedStrategySettingsService:
    """Type-safe strategy settings service using SQLModel"""
    
    def __init__(self):
        pass
    
    def get_settings(
        self, 
        db: Session, 
        strategy_id: int
    ) -> Optional[Union[BTCScalpingSettings, PortfolioDistributorSettings]]:
        """Get typed settings for a strategy"""
        try:
            # Get strategy to determine type
            strategy = db.get(Strategy, strategy_id)
            if not strategy:
                logger.error(f"Strategy {strategy_id} not found")
                return None
            
            strategy_type = StrategyTypeEnum(strategy.strategy_type.value)
            settings_model = StrategySettingsFactory.get_settings_model(strategy_type)
            
            # Query the appropriate settings table
            statement = select(settings_model).where(settings_model.strategy_id == strategy_id)
            settings = db.exec(statement).first()
            
            if not settings:
                logger.info(f"No settings found for strategy {strategy_id}, creating defaults")
                settings = self.create_default_settings(db, strategy_id, strategy_type)
            
            return settings
            
        except Exception as e:
            logger.error(f"Error getting settings for strategy {strategy_id}: {e}")
            return None
    
    def create_default_settings(
        self,
        db: Session,
        strategy_id: int,
        strategy_type: StrategyTypeEnum
    ) -> Optional[Union[BTCScalpingSettings, PortfolioDistributorSettings]]:
        """Create default settings for a strategy"""
        try:
            settings = StrategySettingsFactory.create_default_settings(strategy_type, strategy_id)
            
            db.add(settings)
            db.commit()
            db.refresh(settings)
            
            logger.info(f"Created default {strategy_type.value} settings for strategy {strategy_id}")
            return settings
            
        except Exception as e:
            logger.error(f"Error creating default settings for strategy {strategy_id}: {e}")
            db.rollback()
            return None
    
    def update_settings(
        self,
        db: Session,
        strategy_id: int,
        updates: Dict[str, Any]
    ) -> Optional[Union[BTCScalpingSettings, PortfolioDistributorSettings]]:
        """Update settings for a strategy with validation"""
        try:
            # Get current settings
            current_settings = self.get_settings(db, strategy_id)
            if not current_settings:
                logger.error(f"Cannot update settings for strategy {strategy_id}: not found")
                return None
            
            # Apply updates
            for key, value in updates.items():
                if hasattr(current_settings, key):
                    setattr(current_settings, key, value)
                else:
                    logger.warning(f"Unknown setting key '{key}' for strategy {strategy_id}")
            
            # Update timestamp
            from datetime import datetime
            current_settings.updated_at = datetime.utcnow()
            
            # Validate and save
            db.add(current_settings)
            db.commit()
            db.refresh(current_settings)
            
            logger.info(f"Updated settings for strategy {strategy_id}: {list(updates.keys())}")
            return current_settings
            
        except Exception as e:
            logger.error(f"Error updating settings for strategy {strategy_id}: {e}")
            db.rollback()
            return None
    
    def delete_settings(self, db: Session, strategy_id: int) -> bool:
        """Delete settings for a strategy"""
        try:
            settings = self.get_settings(db, strategy_id)
            if not settings:
                logger.warning(f"No settings to delete for strategy {strategy_id}")
                return True
            
            db.delete(settings)
            db.commit()
            
            logger.info(f"Deleted settings for strategy {strategy_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting settings for strategy {strategy_id}: {e}")
            db.rollback()
            return False
    
    def get_settings_schema(self, strategy_type: StrategyTypeEnum) -> Dict[str, Any]:
        """Get the JSON schema for a strategy type's settings"""
        try:
            settings_model = StrategySettingsFactory.get_settings_model(strategy_type)
            return settings_model.model_json_schema()
        except Exception as e:
            logger.error(f"Error getting schema for {strategy_type}: {e}")
            return {}
    
    def validate_settings(
        self,
        strategy_type: StrategyTypeEnum,
        settings_data: Dict[str, Any]
    ) -> tuple[bool, Optional[str], Optional[Union[BTCScalpingSettings, PortfolioDistributorSettings]]]:
        """Validate settings data against the schema"""
        try:
            settings = StrategySettingsFactory.validate_settings(strategy_type, settings_data)
            return True, None, settings
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Settings validation failed for {strategy_type}: {error_msg}")
            return False, error_msg, None
    
    def migrate_legacy_settings(self, db: Session, strategy_id: int) -> bool:
        """Migrate settings from old StrategySetting table to new typed models"""
        try:
            from database.models import StrategySetting, Strategy
            
            # Get strategy type
            strategy = db.get(Strategy, strategy_id)
            if not strategy:
                logger.error(f"Strategy {strategy_id} not found for migration")
                return False
            
            strategy_type = StrategyTypeEnum(strategy.strategy_type.value)
            
            # Get old settings
            old_settings = db.query(StrategySetting).filter(
                StrategySetting.strategy_id == strategy_id
            ).all()
            
            if not old_settings:
                logger.info(f"No legacy settings to migrate for strategy {strategy_id}")
                return True
            
            # Convert to dictionary
            settings_dict = {}
            for setting in old_settings:
                from services.strategy_settings_service import strategy_settings_service
                value = strategy_settings_service._parse_setting_value(
                    setting.setting_value, setting.setting_type
                )
                settings_dict[setting.setting_key] = value
            
            # Create new typed settings
            settings_model = StrategySettingsFactory.get_settings_model(strategy_type)
            
            # Filter out settings that don't exist in the new model
            model_fields = settings_model.model_fields.keys()
            filtered_settings = {k: v for k, v in settings_dict.items() if k in model_fields}
            filtered_settings['strategy_id'] = strategy_id
            
            # Special handling for portfolio settings
            if strategy_type == StrategyTypeEnum.PORTFOLIO_DISTRIBUTOR:
                # Convert list/dict to JSON strings for storage
                if 'symbols' in filtered_settings and isinstance(filtered_settings['symbols'], list):
                    import json
                    filtered_settings['symbols'] = json.dumps(filtered_settings['symbols'])
                if 'weights' in filtered_settings and isinstance(filtered_settings['weights'], dict):
                    import json  
                    filtered_settings['allocation_weights'] = json.dumps(filtered_settings['weights'])
                    del filtered_settings['weights']  # Remove old key
            
            # Create new settings instance
            new_settings = settings_model(**filtered_settings)
            
            # Save to database
            db.add(new_settings)
            db.commit()
            
            logger.info(f"Migrated settings for strategy {strategy_id} from legacy format")
            return True
            
        except Exception as e:
            logger.error(f"Error migrating legacy settings for strategy {strategy_id}: {e}")
            db.rollback()
            return False

# Global instance
typed_settings_service = TypedStrategySettingsService()