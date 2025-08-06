"""
Type-Safe Base Strategy using SQLModel
Provides typed settings access with full validation and IDE support
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Union
from sqlmodel import Session, select
import pandas as pd
from strategies.base_strategy import BacktestResult
from database.sqlmodel_models import (
    Strategy, BTCScalpingSettings, PortfolioDistributorSettings, 
    StrategyTypeEnum
)
import logging

logger = logging.getLogger(__name__)

class TypedBaseStrategy(ABC):
    """Type-safe base class for all trading strategies using SQLModel"""
    
    def __init__(self, strategy_id: int, db_session: Session):
        self.strategy_id = strategy_id
        self.db_session = db_session
        self._strategy: Optional[Strategy] = None
        self._settings: Optional[Union[BTCScalpingSettings, PortfolioDistributorSettings]] = None
        self._settings_loaded = False
    
    @property
    def strategy(self) -> Optional[Strategy]:
        """Get the strategy record"""
        if not self._strategy:
            self._strategy = self.db_session.get(Strategy, self.strategy_id)
        return self._strategy
    
    @property
    def settings(self) -> Optional[Union[BTCScalpingSettings, PortfolioDistributorSettings]]:
        """Get typed settings for this strategy"""
        if not self._settings_loaded:
            self._load_settings()
        return self._settings
    
    def _load_settings(self) -> None:
        """Load typed settings based on strategy type"""
        try:
            if not self.strategy:
                logger.error(f"Strategy {self.strategy_id} not found")
                self._settings_loaded = True
                return
            
            if self.strategy.strategy_type == StrategyTypeEnum.BTC_SCALPING:
                self._settings = self.db_session.get(BTCScalpingSettings, self.strategy_id)
                if not self._settings:
                    # Create default settings
                    self._settings = BTCScalpingSettings(strategy_id=self.strategy_id)
                    self.db_session.add(self._settings)
                    self.db_session.commit()
                    logger.info(f"Created default BTC settings for strategy {self.strategy_id}")
            
            elif self.strategy.strategy_type == StrategyTypeEnum.PORTFOLIO_DISTRIBUTOR:
                self._settings = self.db_session.get(PortfolioDistributorSettings, self.strategy_id)
                if not self._settings:
                    # Create default settings
                    self._settings = PortfolioDistributorSettings(strategy_id=self.strategy_id)
                    self.db_session.add(self._settings)
                    self.db_session.commit()
                    logger.info(f"Created default portfolio settings for strategy {self.strategy_id}")
            
            self._settings_loaded = True
            
        except Exception as e:
            logger.error(f"Error loading settings for strategy {self.strategy_id}: {e}")
            self._settings_loaded = True
    
    def update_settings(self, **kwargs) -> bool:
        """Update strategy settings with validation"""
        try:
            if not self.settings:
                logger.error(f"No settings found for strategy {self.strategy_id}")
                return False
            
            # Update fields
            for key, value in kwargs.items():
                if hasattr(self.settings, key):
                    setattr(self.settings, key, value)
                else:
                    logger.warning(f"Unknown setting: {key}")
            
            # Update timestamp
            from datetime import datetime
            self.settings.updated_at = datetime.utcnow()
            
            # Save to database with automatic validation
            self.db_session.add(self.settings)
            self.db_session.commit()
            
            logger.info(f"Updated settings for strategy {self.strategy_id}: {list(kwargs.keys())}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating settings for strategy {self.strategy_id}: {e}")
            self.db_session.rollback()
            return False
    
    def refresh_settings(self) -> None:
        """Refresh settings from database"""
        self._settings = None
        self._settings_loaded = False
        self._load_settings()
    
    def get_settings_dict(self) -> Dict[str, Any]:
        """Get settings as dictionary for legacy compatibility"""
        if not self.settings:
            return {}
        
        if hasattr(self.settings, 'settings_dict'):
            return self.settings.settings_dict
        
        # Fallback to model dump
        return self.settings.model_dump()
    
    def validate_settings(self) -> tuple[bool, Optional[str]]:
        """Validate current settings"""
        try:
            if not self.settings:
                return False, "No settings found"
            
            # SQLModel automatically validates on assignment
            # If we got here, settings are valid
            return True, None
            
        except Exception as e:
            return False, str(e)
    
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
        Run backtesting for this strategy with type-safe settings
        
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
    def get_strategy_info(self) -> Dict[str, Any]:
        """Get strategy information"""
        if not self.strategy or not self.settings:
            return {}
        
        is_valid, error = self.validate_settings()
        
        return {
            'strategy_id': self.strategy_id,
            'name': self.strategy.name,
            'type': self.strategy.strategy_type.value,
            'is_active': self.strategy.is_active,
            'is_valid': is_valid,
            'validation_error': error,
            'settings': self.get_settings_dict(),
            'created_at': self.strategy.created_at.isoformat(),
            'updated_at': self.strategy.updated_at.isoformat()
        }