"""
Typed Strategy Settings Models using SQLModel
Provides type-safe, validated settings for different strategy types
"""

from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum
import json

# Strategy Types Enum
class StrategyTypeEnum(str, Enum):
    BTC_SCALPING = "btc_scalping"
    PORTFOLIO_DISTRIBUTOR = "portfolio_distributor"

# Investment Frequency Enum
class InvestmentFrequency(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly" 
    MONTHLY = "monthly"

# Base Settings Model
class StrategySettingsBase(SQLModel):
    """Base class for all strategy settings"""
    strategy_id: int = Field(foreign_key="strategies.id", primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

# BTC Scalping Strategy Settings
class BTCScalpingSettings(StrategySettingsBase, table=True):
    """Type-safe settings for BTC Scalping Strategy"""
    __tablename__ = "btc_scalping_settings"
    
    # Core Trading Parameters
    check_interval: int = Field(
        default=60, 
        ge=10, 
        le=3600,
        description="How often to check for trading signals (seconds)"
    )
    
    position_size: float = Field(
        default=0.001,
        gt=0.0,
        le=1.0,
        description="Amount of BTC to trade per position"
    )
    
    take_profit_pct: float = Field(
        default=0.002,
        gt=0.0,
        le=0.1,
        description="Take profit percentage (0.002 = 0.2%)"
    )
    
    stop_loss_pct: float = Field(
        default=0.001,
        gt=0.0,
        le=0.1,
        description="Stop loss percentage (0.001 = 0.1%)"
    )
    
    # Technical Analysis Parameters
    short_ma_periods: int = Field(
        default=3,
        ge=1,
        le=20,
        description="Short moving average periods"
    )
    
    long_ma_periods: int = Field(
        default=5,
        ge=2,
        le=50,
        description="Long moving average periods"
    )
    
    rsi_oversold: int = Field(
        default=30,
        ge=10,
        le=40,
        description="RSI oversold threshold for buy signals"
    )
    
    rsi_overbought: int = Field(
        default=70,
        ge=60,
        le=90,
        description="RSI overbought threshold for sell signals"
    )
    
    # Risk Management
    max_positions: int = Field(
        default=1,
        ge=1,
        le=5,
        description="Maximum concurrent positions"
    )
    
    min_volume: int = Field(
        default=1000,
        ge=0,
        description="Minimum volume threshold"
    )
    
    # AI Settings
    use_ai_analysis: bool = Field(
        default=True,
        description="Enable AI-enhanced analysis"
    )
    
    ai_confidence_threshold: float = Field(
        default=0.6,
        ge=0.0,
        le=1.0,
        description="Minimum AI confidence threshold"
    )
    
    combine_ai_with_technical: bool = Field(
        default=True,
        description="Combine AI signals with technical analysis"
    )
    
    # Paper Trading
    paper_trading_mode: bool = Field(
        default=True,
        description="Enable paper trading mode"
    )
    
    fallback_volume: int = Field(
        default=10000,
        description="Fallback volume for paper trading"
    )
    
    @property
    def settings_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for legacy compatibility"""
        return {
            "check_interval": self.check_interval,
            "position_size": self.position_size,
            "take_profit_pct": self.take_profit_pct,
            "stop_loss_pct": self.stop_loss_pct,
            "short_ma_periods": self.short_ma_periods,
            "long_ma_periods": self.long_ma_periods,
            "rsi_oversold": self.rsi_oversold,
            "rsi_overbought": self.rsi_overbought,
            "max_positions": self.max_positions,
            "min_volume": self.min_volume,
            "use_ai_analysis": self.use_ai_analysis,
            "ai_confidence_threshold": self.ai_confidence_threshold,
            "combine_ai_with_technical": self.combine_ai_with_technical,
            "paper_trading_mode": self.paper_trading_mode,
            "fallback_volume": self.fallback_volume
        }

# Portfolio Distributor Strategy Settings
class PortfolioDistributorSettings(StrategySettingsBase, table=True):
    """Type-safe settings for Portfolio Distributor Strategy"""
    __tablename__ = "portfolio_distributor_settings"
    
    # Investment Schedule
    check_interval: int = Field(
        default=3600,
        ge=300,
        le=86400,
        description="How often to check for investment opportunities (seconds)"
    )
    
    investment_amount: float = Field(
        default=1000.0,
        gt=0.0,
        le=100000.0,
        description="Dollar amount to invest per cycle"
    )
    
    investment_frequency: InvestmentFrequency = Field(
        default=InvestmentFrequency.WEEKLY,
        description="How often to make new investments"
    )
    
    # Portfolio Composition
    symbols: str = Field(
        default='["SPY", "NVDA", "V", "JNJ", "UNH", "PG", "JPM", "MSFT"]',
        description="JSON array of symbols to include in portfolio"
    )
    
    allocation_weights: str = Field(
        default='{"SPY": 20.0, "NVDA": 15.0, "V": 12.5, "JNJ": 12.5, "UNH": 12.5, "PG": 10.0, "JPM": 10.0, "MSFT": 7.5}',
        description="JSON object with symbol allocation percentages"
    )
    
    # Rebalancing
    rebalance_threshold: float = Field(
        default=5.0,
        ge=1.0,
        le=20.0,
        description="Deviation threshold to trigger rebalancing (%)"
    )
    
    # Risk Management
    max_position_size: float = Field(
        default=0.25,
        gt=0.0,
        le=1.0,
        description="Maximum position size as fraction of portfolio"
    )
    
    min_cash_reserve: float = Field(
        default=0.05,
        ge=0.0,
        le=0.5,
        description="Minimum cash reserve as fraction of portfolio"
    )
    
    @property
    def symbols_list(self) -> List[str]:
        """Get symbols as a list"""
        try:
            return json.loads(self.symbols)
        except (json.JSONDecodeError, TypeError):
            return ["SPY", "NVDA", "V", "JNJ", "UNH", "PG", "JPM", "MSFT"]
    
    @symbols_list.setter
    def symbols_list(self, value: List[str]):
        """Set symbols from a list"""
        self.symbols = json.dumps(value)
    
    @property
    def weights_dict(self) -> Dict[str, float]:
        """Get allocation weights as a dictionary"""
        try:
            return json.loads(self.allocation_weights)
        except (json.JSONDecodeError, TypeError):
            return {
                "SPY": 20.0, "NVDA": 15.0, "V": 12.5, "JNJ": 12.5,
                "UNH": 12.5, "PG": 10.0, "JPM": 10.0, "MSFT": 7.5
            }
    
    @weights_dict.setter
    def weights_dict(self, value: Dict[str, float]):
        """Set allocation weights from a dictionary"""
        self.allocation_weights = json.dumps(value)
    
    @property
    def settings_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for legacy compatibility"""
        return {
            "check_interval": self.check_interval,
            "investment_amount": self.investment_amount,
            "investment_frequency": self.investment_frequency.value,
            "symbols": self.symbols_list,
            "weights": self.weights_dict,
            "rebalance_threshold": self.rebalance_threshold,
            "max_position_size": self.max_position_size,
            "min_cash_reserve": self.min_cash_reserve
        }

# Settings Factory
class StrategySettingsFactory:
    """Factory for creating and managing strategy settings"""
    
    @staticmethod
    def get_settings_model(strategy_type: StrategyTypeEnum) -> type:
        """Get the appropriate settings model for a strategy type"""
        if strategy_type == StrategyTypeEnum.BTC_SCALPING:
            return BTCScalpingSettings
        elif strategy_type == StrategyTypeEnum.PORTFOLIO_DISTRIBUTOR:
            return PortfolioDistributorSettings
        else:
            raise ValueError(f"Unknown strategy type: {strategy_type}")
    
    @staticmethod
    def create_default_settings(strategy_type: StrategyTypeEnum, strategy_id: int) -> Union[BTCScalpingSettings, PortfolioDistributorSettings]:
        """Create default settings instance for a strategy"""
        settings_model = StrategySettingsFactory.get_settings_model(strategy_type)
        return settings_model(strategy_id=strategy_id)
    
    @staticmethod
    def validate_settings(strategy_type: StrategyTypeEnum, settings_data: Dict[str, Any]) -> Union[BTCScalpingSettings, PortfolioDistributorSettings]:
        """Validate and create settings instance from dictionary"""
        settings_model = StrategySettingsFactory.get_settings_model(strategy_type)
        return settings_model(**settings_data)

# Export all models for database creation
__all__ = [
    "StrategyTypeEnum",
    "InvestmentFrequency", 
    "BTCScalpingSettings",
    "PortfolioDistributorSettings",
    "StrategySettingsFactory"
]