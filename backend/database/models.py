from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()

class StrategyType(enum.Enum):
    BTC_SCALPING = "btc_scalping"
    PORTFOLIO_DISTRIBUTOR = "portfolio_distributor"

class OrderStatus(enum.Enum):
    PENDING = "pending"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"

class Strategy(Base):
    __tablename__ = "strategies"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True)
    strategy_type = Column(Enum(StrategyType))
    is_active = Column(Boolean, default=True)
    initial_capital = Column(Float)
    current_capital = Column(Float)
    total_invested = Column(Float, default=0.0)  # Track total amount invested by strategy
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    config = Column(Text)  # JSON string for strategy configuration
    
    # Relationships
    positions = relationship("Position", back_populates="strategy")
    trades = relationship("Trade", back_populates="strategy")
    performance_metrics = relationship("PerformanceMetric", back_populates="strategy")
    event_logs = relationship("StrategyEventLog", back_populates="strategy")
    settings = relationship("StrategySetting", back_populates="strategy")

class Position(Base):
    __tablename__ = "positions"
    
    id = Column(Integer, primary_key=True, index=True)
    strategy_id = Column(Integer, ForeignKey("strategies.id"))
    symbol = Column(String(10), index=True)
    quantity = Column(Float)
    avg_price = Column(Float)
    current_price = Column(Float)
    market_value = Column(Float)
    unrealized_pnl = Column(Float)
    side = Column(String(10))  # long/short
    opened_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    strategy = relationship("Strategy", back_populates="positions")
    trades = relationship("Trade", back_populates="position")

class Trade(Base):
    __tablename__ = "trades"
    
    id = Column(Integer, primary_key=True, index=True)
    strategy_id = Column(Integer, ForeignKey("strategies.id"))
    position_id = Column(Integer, ForeignKey("positions.id"), nullable=True)
    alpaca_order_id = Column(String(50), unique=True, index=True)
    symbol = Column(String(10), index=True)
    side = Column(String(10))  # buy/sell
    quantity = Column(Float)
    price = Column(Float)
    commission = Column(Float, default=0.0)
    realized_pnl = Column(Float, default=0.0)
    status = Column(Enum(OrderStatus))
    executed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    strategy = relationship("Strategy", back_populates="trades")
    position = relationship("Position", back_populates="trades")

class PerformanceMetric(Base):
    __tablename__ = "performance_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    strategy_id = Column(Integer, ForeignKey("strategies.id"))
    date = Column(DateTime, index=True)
    total_value = Column(Float)  # positions + cash
    daily_pnl = Column(Float)
    cumulative_pnl = Column(Float)
    roi_percentage = Column(Float)
    sharpe_ratio = Column(Float, nullable=True)
    max_drawdown = Column(Float, nullable=True)
    win_rate = Column(Float, nullable=True)
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)
    
    # Relationships
    strategy = relationship("Strategy", back_populates="performance_metrics")

class Portfolio(Base):
    __tablename__ = "portfolios"
    
    id = Column(Integer, primary_key=True, index=True)
    strategy_id = Column(Integer, ForeignKey("strategies.id"))
    name = Column(String(100))
    symbols = Column(Text)  # JSON array of stock symbols
    allocation_weights = Column(Text)  # JSON object with symbol: weight mapping
    investment_frequency = Column(String(20))  # weekly, monthly, etc.
    next_investment_date = Column(DateTime)
    investment_amount = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

class EventLogLevel(enum.Enum):
    DEBUG = "debug"
    INFO = "info"
    WARN = "warn"
    ERROR = "error"
    CRITICAL = "critical"

class SettingType(enum.Enum):
    INTEGER = "integer"
    FLOAT = "float"
    STRING = "string"
    BOOLEAN = "boolean"
    JSON = "json"

class StrategySetting(Base):
    __tablename__ = "strategy_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    strategy_id = Column(Integer, ForeignKey("strategies.id"))
    setting_key = Column(String(50), index=True)
    setting_value = Column(Text)
    setting_type = Column(Enum(SettingType))
    description = Column(String(200))
    default_value = Column(Text)
    is_required = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    strategy = relationship("Strategy", back_populates="settings")

class StrategyEventLog(Base):
    __tablename__ = "strategy_event_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    strategy_id = Column(Integer, ForeignKey("strategies.id"))
    level = Column(Enum(EventLogLevel), default=EventLogLevel.INFO)
    event_type = Column(String(50))  # "trade_check", "signal_generated", "order_placed", "risk_alert", etc.
    message = Column(Text)
    details = Column(Text)  # JSON string for additional event data
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    strategy = relationship("Strategy", back_populates="event_logs")