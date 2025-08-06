from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List
from sqlalchemy.orm import Session
from dataclasses import dataclass
from datetime import datetime
import pandas as pd
from services.strategy_settings_service import strategy_settings_service, SettingType
import logging

logger = logging.getLogger(__name__)

@dataclass
class BacktestTrade:
    """Represents a trade executed during backtesting"""
    timestamp: datetime
    symbol: str
    side: str  # 'buy' or 'sell'
    quantity: float
    price: float
    commission: float = 0.0
    pnl: Optional[float] = None
    reason: str = ""

@dataclass  
class BacktestResult:
    """Comprehensive backtesting results"""
    strategy_type: str
    symbol: str
    period: str
    start_date: datetime
    end_date: datetime
    initial_capital: float
    final_capital: float
    total_return: float
    total_return_pct: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    max_drawdown: float
    sharpe_ratio: float
    trades: List[BacktestTrade]
    equity_curve: List[Dict]  # [{date: datetime, value: float}, ...]
    metadata: Dict[str, Any]  # Strategy-specific additional data

class BaseStrategy(ABC):
    """Base class for all trading strategies with settings management"""
    
    def __init__(self, strategy_id: int, db_session: Session):
        self.strategy_id = strategy_id
        self.db_session = db_session
        self._settings_cache = {}
        self._cache_loaded = False
    
    def _load_settings_cache(self) -> None:
        """Load all settings into cache for performance"""
        if not self._cache_loaded:
            self._settings_cache = strategy_settings_service.get_all_settings(
                self.db_session, self.strategy_id
            )
            self._cache_loaded = True
            logger.debug(f"Loaded settings cache for strategy {self.strategy_id}")
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a setting value with optional default"""
        self._load_settings_cache()
        return self._settings_cache.get(key, default)
    
    def set_setting(self, key: str, value: Any, setting_type: SettingType, 
                   description: str = "", is_required: bool = False) -> bool:
        """Set a setting value and update cache"""
        success = strategy_settings_service.set_setting(
            db=self.db_session,
            strategy_id=self.strategy_id,
            setting_key=key,
            value=value,
            setting_type=setting_type,
            description=description,
            is_required=is_required
        )
        
        if success:
            # Update cache
            self._settings_cache[key] = value
            
        return success
    
    def get_int_setting(self, key: str, default: int = 0) -> int:
        """Get an integer setting"""
        value = self.get_setting(key, default)
        try:
            return int(value)
        except (ValueError, TypeError):
            logger.warning(f"Invalid integer setting {key}={value}, using default {default}")
            return default
    
    def get_float_setting(self, key: str, default: float = 0.0) -> float:
        """Get a float setting"""
        value = self.get_setting(key, default)
        try:
            return float(value)
        except (ValueError, TypeError):
            logger.warning(f"Invalid float setting {key}={value}, using default {default}")
            return default
    
    def get_bool_setting(self, key: str, default: bool = False) -> bool:
        """Get a boolean setting"""
        value = self.get_setting(key, default)
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ('true', '1', 'yes', 'on')
        try:
            return bool(int(value))
        except (ValueError, TypeError):
            logger.warning(f"Invalid boolean setting {key}={value}, using default {default}")
            return default
    
    def get_list_setting(self, key: str, default: list = None) -> list:
        """Get a list setting (JSON array)"""
        if default is None:
            default = []
        value = self.get_setting(key, default)
        if isinstance(value, list):
            return value
        logger.warning(f"Invalid list setting {key}={value}, using default {default}")
        return default
    
    def get_dict_setting(self, key: str, default: dict = None) -> dict:
        """Get a dictionary setting (JSON object)"""
        if default is None:
            default = {}
        value = self.get_setting(key, default)
        if isinstance(value, dict):
            return value
        logger.warning(f"Invalid dict setting {key}={value}, using default {default}")
        return default
    
    def initialize_default_settings(self, strategy_type: str) -> bool:
        """Initialize default settings for this strategy"""
        return strategy_settings_service.initialize_default_settings(
            self.db_session, self.strategy_id, strategy_type
        )
    
    def refresh_settings(self) -> None:
        """Refresh settings cache from database"""
        self._cache_loaded = False
        self._load_settings_cache()
    
    def get_all_settings(self) -> Dict[str, Any]:
        """Get all settings as a dictionary"""
        self._load_settings_cache()
        return self._settings_cache.copy()
    
    # Abstract methods that must be implemented by subclasses
    @abstractmethod
    def run_iteration(self) -> None:
        """Run one iteration of the strategy"""
        pass
    
    @abstractmethod
    def start(self) -> bool:
        """Start the strategy (setup, validation, etc.)"""
        pass
    
    @abstractmethod
    def stop(self) -> bool:
        """Stop the strategy (cleanup, etc.)"""
        pass
    
    @abstractmethod
    def backtest(self, data: pd.DataFrame, config: Dict[str, Any], 
                initial_capital: float, days_back: int) -> BacktestResult:
        """
        Run backtesting for this strategy
        
        Args:
            data: Historical price data with columns [timestamp, open, high, low, close, volume]
            config: Strategy-specific configuration parameters
            initial_capital: Starting capital for backtesting
            days_back: Number of days to backtest
            
        Returns:
            BacktestResult: Comprehensive backtesting results
        """
        pass
    
    # Optional methods that can be overridden
    def validate_settings(self) -> bool:
        """Validate strategy settings - override in subclass if needed"""
        return True
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """Get strategy information - can be overridden"""
        return {
            'strategy_id': self.strategy_id,
            'settings_count': len(self._settings_cache) if self._cache_loaded else 0,
            'is_valid': self.validate_settings()
        }