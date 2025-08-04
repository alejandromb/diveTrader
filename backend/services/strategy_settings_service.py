import json
from typing import Any, Dict, List, Optional, Union
from sqlalchemy.orm import Session
from database.models import Strategy, StrategySetting, SettingType
import logging

logger = logging.getLogger(__name__)

class StrategySettingsService:
    """Service for managing strategy settings in the database"""
    
    def __init__(self):
        pass
    
    def get_setting(self, db: Session, strategy_id: int, setting_key: str) -> Optional[Any]:
        """Get a specific setting value for a strategy"""
        setting = db.query(StrategySetting).filter(
            StrategySetting.strategy_id == strategy_id,
            StrategySetting.setting_key == setting_key
        ).first()
        
        if not setting:
            return None
            
        return self._parse_setting_value(setting.setting_value, setting.setting_type)
    
    def get_all_settings(self, db: Session, strategy_id: int) -> Dict[str, Any]:
        """Get all settings for a strategy as a dictionary"""
        settings = db.query(StrategySetting).filter(
            StrategySetting.strategy_id == strategy_id
        ).all()
        
        result = {}
        for setting in settings:
            result[setting.setting_key] = self._parse_setting_value(
                setting.setting_value, setting.setting_type
            )
        
        return result
    
    def set_setting(self, db: Session, strategy_id: int, setting_key: str, 
                   value: Any, setting_type: SettingType, 
                   description: str = "", default_value: Any = None,
                   is_required: bool = False) -> bool:
        """Set a setting value for a strategy"""
        try:
            # Check if setting already exists
            existing_setting = db.query(StrategySetting).filter(
                StrategySetting.strategy_id == strategy_id,
                StrategySetting.setting_key == setting_key
            ).first()
            
            # Convert value to string for storage
            value_str = self._serialize_setting_value(value, setting_type)
            default_str = self._serialize_setting_value(default_value, setting_type) if default_value is not None else None
            
            if existing_setting:
                # Update existing setting
                existing_setting.setting_value = value_str
                existing_setting.setting_type = setting_type
                existing_setting.description = description
                existing_setting.default_value = default_str
                existing_setting.is_required = is_required
            else:
                # Create new setting
                new_setting = StrategySetting(
                    strategy_id=strategy_id,
                    setting_key=setting_key,
                    setting_value=value_str,
                    setting_type=setting_type,
                    description=description,
                    default_value=default_str,
                    is_required=is_required
                )
                db.add(new_setting)
            
            db.commit()
            logger.info(f"Set setting {setting_key}={value} for strategy {strategy_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error setting {setting_key} for strategy {strategy_id}: {e}")
            db.rollback()
            return False
    
    def delete_setting(self, db: Session, strategy_id: int, setting_key: str) -> bool:
        """Delete a setting for a strategy"""
        try:
            setting = db.query(StrategySetting).filter(
                StrategySetting.strategy_id == strategy_id,
                StrategySetting.setting_key == setting_key
            ).first()
            
            if setting:
                db.delete(setting)
                db.commit()
                logger.info(f"Deleted setting {setting_key} for strategy {strategy_id}")
                return True
            else:
                logger.warning(f"Setting {setting_key} not found for strategy {strategy_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting setting {setting_key} for strategy {strategy_id}: {e}")
            db.rollback()
            return False
    
    def get_setting_with_default(self, db: Session, strategy_id: int, 
                                setting_key: str, default_value: Any = None) -> Any:
        """Get a setting value or return default if not found"""
        value = self.get_setting(db, strategy_id, setting_key)
        return value if value is not None else default_value
    
    def initialize_default_settings(self, db: Session, strategy_id: int, strategy_type: str) -> bool:
        """Initialize default settings for a strategy based on its type"""
        try:
            default_settings = self._get_default_settings_for_type(strategy_type)
            
            for key, config in default_settings.items():
                self.set_setting(
                    db=db,
                    strategy_id=strategy_id,
                    setting_key=key,
                    value=config['value'],
                    setting_type=config['type'],
                    description=config.get('description', ''),
                    default_value=config['value'],
                    is_required=config.get('required', False)
                )
            
            logger.info(f"Initialized default settings for strategy {strategy_id} ({strategy_type})")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing default settings for strategy {strategy_id}: {e}")
            return False
    
    def _parse_setting_value(self, value: str, setting_type: SettingType) -> Any:
        """Parse a string value based on its type"""
        if value is None or value == "":
            return None
            
        try:
            if setting_type == SettingType.INTEGER:
                return int(value)
            elif setting_type == SettingType.FLOAT:
                return float(value)
            elif setting_type == SettingType.BOOLEAN:
                return value.lower() in ('true', '1', 'yes', 'on')
            elif setting_type == SettingType.JSON:
                return json.loads(value)
            else:  # STRING
                return value
        except (ValueError, json.JSONDecodeError) as e:
            logger.error(f"Error parsing setting value '{value}' as {setting_type}: {e}")
            return value  # Return as string if parsing fails
    
    def _serialize_setting_value(self, value: Any, setting_type: SettingType) -> str:
        """Serialize a value to string for database storage"""
        if value is None:
            return ""
            
        if setting_type == SettingType.JSON:
            return json.dumps(value)
        else:
            return str(value)
    
    def _get_default_settings_for_type(self, strategy_type: str) -> Dict[str, Dict]:
        """Get default settings configuration for each strategy type"""
        if strategy_type == "btc_scalping":
            return {
                "check_interval": {
                    "value": 60,
                    "type": SettingType.INTEGER,
                    "description": "How often to check for trading signals (seconds)",
                    "required": True
                },
                "position_size": {
                    "value": 0.001,
                    "type": SettingType.FLOAT,
                    "description": "Amount of BTC to trade per position",
                    "required": True
                },
                "take_profit_pct": {
                    "value": 0.002,
                    "type": SettingType.FLOAT,
                    "description": "Take profit percentage (0.002 = 0.2%)",
                    "required": True
                },
                "stop_loss_pct": {
                    "value": 0.001,
                    "type": SettingType.FLOAT,
                    "description": "Stop loss percentage (0.001 = 0.1%)",
                    "required": True
                },
                "rsi_oversold": {
                    "value": 30,
                    "type": SettingType.INTEGER,
                    "description": "RSI oversold threshold for buy signals",
                    "required": False
                },
                "rsi_overbought": {
                    "value": 70,
                    "type": SettingType.INTEGER,
                    "description": "RSI overbought threshold for sell signals",
                    "required": False
                }
            }
        elif strategy_type == "portfolio_distributor":
            return {
                "check_interval": {
                    "value": 3600,
                    "type": SettingType.INTEGER,
                    "description": "How often to check for rebalancing (seconds)",
                    "required": True
                },
                "investment_amount": {
                    "value": 1000.0,
                    "type": SettingType.FLOAT,
                    "description": "Dollar amount to invest per cycle (e.g., $1000 weekly)",
                    "required": True
                },
                "symbols": {
                    "value": ["SPY", "NVDA", "V", "JNJ", "UNH", "PG", "JPM", "MSFT"],
                    "type": SettingType.JSON,
                    "description": "List of symbols to include in portfolio",
                    "required": True
                },
                "weights": {
                    "value": {
                        "SPY": 20.0, "NVDA": 15.0, "V": 12.5, "JNJ": 12.5,
                        "UNH": 12.5, "PG": 10.0, "JPM": 10.0, "MSFT": 7.5
                    },
                    "type": SettingType.JSON,
                    "description": "Allocation weights for each symbol (percentages)",
                    "required": True
                },
                "rebalance_threshold": {
                    "value": 5.0,
                    "type": SettingType.FLOAT,
                    "description": "Deviation threshold to trigger rebalancing (%)",
                    "required": False
                },
                "investment_frequency": {
                    "value": "weekly",
                    "type": SettingType.STRING,
                    "description": "How often to make new investments (weekly, monthly)",
                    "required": True
                }
            }
        else:
            return {}

# Global settings service instance
strategy_settings_service = StrategySettingsService()