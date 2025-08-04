"""
Complete SQLModel-based database models for DiveTrader
Replaces the old SQLAlchemy models with type-safe SQLModel equivalents
"""

from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import json

# Enums
class StrategyTypeEnum(str, Enum):
    BTC_SCALPING = "btc_scalping"
    PORTFOLIO_DISTRIBUTOR = "portfolio_distributor"

class OrderStatusEnum(str, Enum):
    PENDING = "pending"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"

class EventLogLevelEnum(str, Enum):
    DEBUG = "debug"
    INFO = "info"
    WARN = "warn"
    ERROR = "error"
    CRITICAL = "critical"

class InvestmentFrequencyEnum(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"

# Core Models
class Strategy(SQLModel, table=True):
    """Main strategy configuration and state"""
    __tablename__ = "strategies"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=100, unique=True, index=True)
    strategy_type: StrategyTypeEnum
    is_active: bool = Field(default=True)
    initial_capital: float = Field(gt=0)
    current_capital: float = Field(gt=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    config: Optional[str] = Field(default=None)  # Legacy JSON config, will be deprecated
    
    # Relationships
    positions: List["Position"] = Relationship(back_populates="strategy")
    trades: List["Trade"] = Relationship(back_populates="strategy")
    performance_metrics: List["PerformanceMetric"] = Relationship(back_populates="strategy")
    event_logs: List["StrategyEventLog"] = Relationship(back_populates="strategy")
    portfolio: Optional["Portfolio"] = Relationship(back_populates="strategy")
    btc_settings: Optional["BTCScalpingSettings"] = Relationship(back_populates="strategy")
    portfolio_settings: Optional["PortfolioDistributorSettings"] = Relationship(back_populates="strategy")

class Position(SQLModel, table=True):
    """Open positions for strategies"""
    __tablename__ = "positions"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    strategy_id: int = Field(foreign_key="strategies.id")
    symbol: str = Field(max_length=10, index=True)
    quantity: float
    avg_price: float = Field(gt=0)
    current_price: float = Field(gt=0)
    market_value: float
    unrealized_pnl: float
    side: str = Field(max_length=10)  # long/short
    opened_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    strategy: Strategy = Relationship(back_populates="positions")
    trades: List["Trade"] = Relationship(back_populates="position")

class Trade(SQLModel, table=True):
    """Executed trades"""
    __tablename__ = "trades"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    strategy_id: int = Field(foreign_key="strategies.id")
    position_id: Optional[int] = Field(default=None, foreign_key="positions.id")
    alpaca_order_id: str = Field(max_length=50, unique=True, index=True)
    symbol: str = Field(max_length=10, index=True)
    side: str = Field(max_length=10)  # buy/sell
    quantity: float = Field(gt=0)
    price: float = Field(gt=0)
    commission: float = Field(default=0.0, ge=0)
    realized_pnl: float = Field(default=0.0)
    status: OrderStatusEnum
    executed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    strategy: Strategy = Relationship(back_populates="trades")
    position: Optional[Position] = Relationship(back_populates="trades")

class PerformanceMetric(SQLModel, table=True):
    """Strategy performance tracking"""
    __tablename__ = "performance_metrics"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    strategy_id: int = Field(foreign_key="strategies.id")
    date: datetime = Field(index=True)
    total_value: float = Field(ge=0)  # positions + cash
    daily_pnl: float
    cumulative_pnl: float
    roi_percentage: float
    sharpe_ratio: Optional[float] = None
    max_drawdown: Optional[float] = None
    win_rate: Optional[float] = Field(default=None, ge=0, le=1)
    total_trades: int = Field(default=0, ge=0)
    winning_trades: int = Field(default=0, ge=0)
    losing_trades: int = Field(default=0, ge=0)
    
    # Relationships
    strategy: Strategy = Relationship(back_populates="performance_metrics")

class Portfolio(SQLModel, table=True):
    """Portfolio configuration for distributor strategy"""
    __tablename__ = "portfolios"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    strategy_id: int = Field(foreign_key="strategies.id")
    name: str = Field(max_length=100)
    symbols: str  # JSON array of stock symbols
    allocation_weights: str  # JSON object with symbol: weight mapping
    investment_frequency: InvestmentFrequencyEnum = Field(default=InvestmentFrequencyEnum.WEEKLY)
    next_investment_date: Optional[datetime] = None
    investment_amount: float = Field(gt=0, default=1000.0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    strategy: Strategy = Relationship(back_populates="portfolio")
    
    @property
    def symbols_list(self) -> List[str]:
        """Get symbols as a list"""
        try:
            return json.loads(self.symbols)
        except (json.JSONDecodeError, TypeError):
            return []
    
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
            return {}
    
    @weights_dict.setter
    def weights_dict(self, value: Dict[str, float]):
        """Set allocation weights from a dictionary"""
        self.allocation_weights = json.dumps(value)

class StrategyEventLog(SQLModel, table=True):
    """Event logging for strategies"""
    __tablename__ = "strategy_event_logs"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    strategy_id: int = Field(foreign_key="strategies.id")
    level: EventLogLevelEnum = Field(default=EventLogLevelEnum.INFO)
    event_type: str = Field(max_length=50)  # "trade_check", "signal_generated", etc.
    message: str
    details: Optional[str] = None  # JSON string for additional event data
    timestamp: datetime = Field(default_factory=datetime.utcnow, index=True)
    
    # Relationships
    strategy: Strategy = Relationship(back_populates="event_logs")

# Strategy Settings Models (Import from separate file)
class BTCScalpingSettings(SQLModel, table=True):
    """Type-safe settings for BTC Scalping Strategy"""
    __tablename__ = "btc_scalping_settings"
    
    strategy_id: int = Field(foreign_key="strategies.id", primary_key=True)
    
    # Core Trading Parameters
    check_interval: int = Field(default=60, ge=10, le=3600)
    position_size: float = Field(default=0.001, gt=0.0, le=1.0)
    take_profit_pct: float = Field(default=0.002, gt=0.0, le=0.1)
    stop_loss_pct: float = Field(default=0.001, gt=0.0, le=0.1)
    
    # Technical Analysis
    short_ma_periods: int = Field(default=3, ge=1, le=20)
    long_ma_periods: int = Field(default=5, ge=2, le=50)
    rsi_oversold: int = Field(default=30, ge=10, le=40)
    rsi_overbought: int = Field(default=70, ge=60, le=90)
    
    # Risk Management
    max_positions: int = Field(default=1, ge=1, le=5)
    min_volume: int = Field(default=1000, ge=0)
    
    # AI Settings
    use_ai_analysis: bool = Field(default=True)
    ai_confidence_threshold: float = Field(default=0.6, ge=0.0, le=1.0)
    combine_ai_with_technical: bool = Field(default=True)
    
    # Paper Trading
    paper_trading_mode: bool = Field(default=True)
    fallback_volume: int = Field(default=10000)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    strategy: Strategy = Relationship(back_populates="btc_settings")

class PortfolioDistributorSettings(SQLModel, table=True):
    """Type-safe settings for Portfolio Distributor Strategy"""
    __tablename__ = "portfolio_distributor_settings"
    
    strategy_id: int = Field(foreign_key="strategies.id", primary_key=True)
    
    # Investment Schedule
    check_interval: int = Field(default=3600, ge=300, le=86400)
    investment_amount: float = Field(default=1000.0, gt=0.0, le=100000.0)
    investment_frequency: InvestmentFrequencyEnum = Field(default=InvestmentFrequencyEnum.WEEKLY)
    
    # Portfolio Composition (JSON strings for complex data)
    symbols: str = Field(default='["SPY", "NVDA", "V", "JNJ", "UNH", "PG", "JPM", "MSFT"]')
    allocation_weights: str = Field(default='{"SPY": 20.0, "NVDA": 15.0, "V": 12.5, "JNJ": 12.5, "UNH": 12.5, "PG": 10.0, "JPM": 10.0, "MSFT": 7.5}')
    
    # Rebalancing
    rebalance_threshold: float = Field(default=5.0, ge=1.0, le=20.0)
    
    # Risk Management
    max_position_size: float = Field(default=0.25, gt=0.0, le=1.0)
    min_cash_reserve: float = Field(default=0.05, ge=0.0, le=0.5)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    strategy: Strategy = Relationship(back_populates="portfolio_settings")
    
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

# Legacy Settings (will be deprecated after migration)
class LegacyStrategySetting(SQLModel, table=True):
    """Legacy settings table - will be deprecated"""
    __tablename__ = "strategy_settings_legacy"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    strategy_id: int = Field(foreign_key="strategies.id")
    setting_key: str = Field(max_length=50, index=True)
    setting_value: str
    setting_type: str = Field(max_length=20)
    description: Optional[str] = Field(default=None, max_length=200)
    default_value: Optional[str] = None
    is_required: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

# Export all models
__all__ = [
    "StrategyTypeEnum",
    "OrderStatusEnum", 
    "EventLogLevelEnum",
    "InvestmentFrequencyEnum",
    "Strategy",
    "Position",
    "Trade",
    "PerformanceMetric",
    "Portfolio",
    "StrategyEventLog",
    "BTCScalpingSettings",
    "PortfolioDistributorSettings",
    "LegacyStrategySetting"
]