#!/usr/bin/env python3
"""
Migration script from old SQLAlchemy models to new SQLModel tables
Preserves all existing data while upgrading to type-safe models
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlmodel import Session, select
from sqlalchemy import create_engine as legacy_create_engine
from sqlalchemy.orm import sessionmaker as legacy_sessionmaker
import logging
from datetime import datetime
import json

# Import old and new models
from database.database import DATABASE_URL as LEGACY_DATABASE_URL
from database.sqlmodel_database import engine as new_engine, init_database
from database.sqlmodel_models import (
    Strategy as NewStrategy,
    Position as NewPosition, 
    Trade as NewTrade,
    PerformanceMetric as NewPerformanceMetric,
    Portfolio as NewPortfolio,
    StrategyEventLog as NewStrategyEventLog,
    BTCScalpingSettings,
    PortfolioDistributorSettings,
    StrategyTypeEnum,
    OrderStatusEnum,
    EventLogLevelEnum,
    InvestmentFrequencyEnum
)

# Import legacy models
try:
    from database.models import (
        Strategy as LegacyStrategy,
        Position as LegacyPosition,
        Trade as LegacyTrade, 
        PerformanceMetric as LegacyPerformanceMetric,
        Portfolio as LegacyPortfolio,
        StrategyEventLog as LegacyStrategyEventLog,
        StrategySetting as LegacyStrategySetting
    )
except ImportError as e:
    print(f"Could not import legacy models: {e}")
    sys.exit(1)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Legacy database connection
legacy_engine = legacy_create_engine(LEGACY_DATABASE_URL)
LegacySessionLocal = legacy_sessionmaker(autocommit=False, autoflush=False, bind=legacy_engine)

class SQLModelMigration:
    """Handles migration from legacy SQLAlchemy to SQLModel"""
    
    def __init__(self):
        self.legacy_session = None
        self.new_session = None
        
    def __enter__(self):
        self.legacy_session = LegacySessionLocal()
        self.new_session = Session(new_engine)
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.legacy_session:
            self.legacy_session.close()
        if self.new_session:
            self.new_session.close()
    
    def migrate_strategies(self) -> bool:
        """Migrate Strategy table"""
        try:
            logger.info("Migrating strategies...")
            
            legacy_strategies = self.legacy_session.query(LegacyStrategy).all()
            logger.info(f"Found {len(legacy_strategies)} strategies to migrate")
            
            for legacy_strategy in legacy_strategies:
                # Check if already exists
                existing = self.new_session.get(NewStrategy, legacy_strategy.id)
                if existing:
                    logger.info(f"Strategy {legacy_strategy.id} already exists, skipping")
                    continue
                
                new_strategy = NewStrategy(
                    id=legacy_strategy.id,
                    name=legacy_strategy.name,
                    strategy_type=StrategyTypeEnum(legacy_strategy.strategy_type.value),
                    is_active=legacy_strategy.is_active,
                    initial_capital=legacy_strategy.initial_capital,
                    current_capital=legacy_strategy.current_capital,
                    created_at=legacy_strategy.created_at,
                    updated_at=legacy_strategy.updated_at,
                    config=legacy_strategy.config
                )
                
                self.new_session.add(new_strategy)
                logger.info(f"Migrated strategy: {legacy_strategy.name}")
            
            self.new_session.commit()
            logger.info("✅ Strategies migration completed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error migrating strategies: {e}")
            self.new_session.rollback()
            return False
    
    def migrate_positions(self) -> bool:
        """Migrate Position table"""
        try:
            logger.info("Migrating positions...")
            
            legacy_positions = self.legacy_session.query(LegacyPosition).all()
            logger.info(f"Found {len(legacy_positions)} positions to migrate")
            
            for legacy_position in legacy_positions:
                existing = self.new_session.get(NewPosition, legacy_position.id)
                if existing:
                    continue
                
                new_position = NewPosition(
                    id=legacy_position.id,
                    strategy_id=legacy_position.strategy_id,
                    symbol=legacy_position.symbol,
                    quantity=legacy_position.quantity,
                    avg_price=legacy_position.avg_price,
                    current_price=legacy_position.current_price,
                    market_value=legacy_position.market_value,
                    unrealized_pnl=legacy_position.unrealized_pnl,
                    side=legacy_position.side,
                    opened_at=legacy_position.opened_at,
                    updated_at=legacy_position.updated_at
                )
                
                self.new_session.add(new_position)
            
            self.new_session.commit()
            logger.info("✅ Positions migration completed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error migrating positions: {e}")
            self.new_session.rollback()
            return False
    
    def migrate_trades(self) -> bool:
        """Migrate Trade table"""
        try:
            logger.info("Migrating trades...")
            
            legacy_trades = self.legacy_session.query(LegacyTrade).all()
            logger.info(f"Found {len(legacy_trades)} trades to migrate")
            
            for legacy_trade in legacy_trades:
                existing = self.new_session.get(NewTrade, legacy_trade.id)
                if existing:
                    continue
                
                new_trade = NewTrade(
                    id=legacy_trade.id,
                    strategy_id=legacy_trade.strategy_id,
                    position_id=legacy_trade.position_id,
                    alpaca_order_id=legacy_trade.alpaca_order_id,
                    symbol=legacy_trade.symbol,
                    side=legacy_trade.side,
                    quantity=legacy_trade.quantity,
                    price=legacy_trade.price,
                    commission=legacy_trade.commission,
                    realized_pnl=legacy_trade.realized_pnl,
                    status=OrderStatusEnum(legacy_trade.status.value),
                    executed_at=legacy_trade.executed_at,
                    created_at=legacy_trade.created_at
                )
                
                self.new_session.add(new_trade)
            
            self.new_session.commit()
            logger.info("✅ Trades migration completed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error migrating trades: {e}")
            self.new_session.rollback()
            return False
    
    def migrate_performance_metrics(self) -> bool:
        """Migrate PerformanceMetric table"""
        try:
            logger.info("Migrating performance metrics...")
            
            legacy_metrics = self.legacy_session.query(LegacyPerformanceMetric).all()
            logger.info(f"Found {len(legacy_metrics)} performance metrics to migrate")
            
            for legacy_metric in legacy_metrics:
                existing = self.new_session.get(NewPerformanceMetric, legacy_metric.id)
                if existing:
                    continue
                
                new_metric = NewPerformanceMetric(
                    id=legacy_metric.id,
                    strategy_id=legacy_metric.strategy_id,
                    date=legacy_metric.date,
                    total_value=legacy_metric.total_value,
                    daily_pnl=legacy_metric.daily_pnl,
                    cumulative_pnl=legacy_metric.cumulative_pnl,
                    roi_percentage=legacy_metric.roi_percentage,
                    sharpe_ratio=legacy_metric.sharpe_ratio,
                    max_drawdown=legacy_metric.max_drawdown,
                    win_rate=legacy_metric.win_rate,
                    total_trades=legacy_metric.total_trades,
                    winning_trades=legacy_metric.winning_trades,
                    losing_trades=legacy_metric.losing_trades
                )
                
                self.new_session.add(new_metric)
            
            self.new_session.commit()
            logger.info("✅ Performance metrics migration completed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error migrating performance metrics: {e}")
            self.new_session.rollback()
            return False
    
    def migrate_portfolios(self) -> bool:
        """Migrate Portfolio table"""
        try:
            logger.info("Migrating portfolios...")
            
            legacy_portfolios = self.legacy_session.query(LegacyPortfolio).all()
            logger.info(f"Found {len(legacy_portfolios)} portfolios to migrate")
            
            for legacy_portfolio in legacy_portfolios:
                existing = self.new_session.get(NewPortfolio, legacy_portfolio.id)
                if existing:
                    continue
                
                new_portfolio = NewPortfolio(
                    id=legacy_portfolio.id,
                    strategy_id=legacy_portfolio.strategy_id,
                    name=legacy_portfolio.name,
                    symbols=legacy_portfolio.symbols,
                    allocation_weights=legacy_portfolio.allocation_weights,
                    investment_frequency=InvestmentFrequencyEnum(legacy_portfolio.investment_frequency),
                    next_investment_date=legacy_portfolio.next_investment_date,
                    investment_amount=legacy_portfolio.investment_amount,
                    created_at=legacy_portfolio.created_at
                )
                
                self.new_session.add(new_portfolio)
            
            self.new_session.commit()
            logger.info("✅ Portfolios migration completed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error migrating portfolios: {e}")
            self.new_session.rollback()
            return False
    
    def migrate_event_logs(self) -> bool:
        """Migrate StrategyEventLog table"""
        try:
            logger.info("Migrating event logs...")
            
            legacy_logs = self.legacy_session.query(LegacyStrategyEventLog).all()
            logger.info(f"Found {len(legacy_logs)} event logs to migrate")
            
            for legacy_log in legacy_logs:
                existing = self.new_session.get(NewStrategyEventLog, legacy_log.id)
                if existing:
                    continue
                
                new_log = NewStrategyEventLog(
                    id=legacy_log.id,
                    strategy_id=legacy_log.strategy_id,
                    level=EventLogLevelEnum(legacy_log.level.value),
                    event_type=legacy_log.event_type,
                    message=legacy_log.message,
                    details=legacy_log.details,
                    timestamp=legacy_log.timestamp
                )
                
                self.new_session.add(new_log)
            
            self.new_session.commit()
            logger.info("✅ Event logs migration completed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error migrating event logs: {e}")
            self.new_session.rollback()
            return False
    
    def migrate_strategy_settings(self) -> bool:
        """Migrate strategy settings to typed models"""
        try:
            logger.info("Migrating strategy settings to typed models...")
            
            # Get all strategies first
            strategies = self.new_session.exec(select(NewStrategy)).all()
            
            for strategy in strategies:
                logger.info(f"Migrating settings for strategy {strategy.id} ({strategy.strategy_type.value})")
                
                # Get legacy settings
                legacy_settings = self.legacy_session.query(LegacyStrategySetting).filter(
                    LegacyStrategySetting.strategy_id == strategy.id
                ).all()
                
                if not legacy_settings:
                    logger.info(f"No legacy settings found for strategy {strategy.id}")
                    continue
                
                # Convert to dict
                settings_dict = {}
                for setting in legacy_settings:
                    from services.strategy_settings_service import strategy_settings_service
                    value = strategy_settings_service._parse_setting_value(
                        setting.setting_value, setting.setting_type
                    )
                    settings_dict[setting.setting_key] = value
                
                # Create typed settings based on strategy type
                if strategy.strategy_type == StrategyTypeEnum.BTC_SCALPING:
                    # Check if already exists
                    existing = self.new_session.get(BTCScalpingSettings, strategy.id)
                    if existing:
                        logger.info(f"BTC settings already exist for strategy {strategy.id}")
                        continue
                    
                    # Filter and create BTC settings
                    btc_fields = BTCScalpingSettings.model_fields.keys()
                    filtered_settings = {k: v for k, v in settings_dict.items() if k in btc_fields}
                    filtered_settings['strategy_id'] = strategy.id
                    
                    btc_settings = BTCScalpingSettings(**filtered_settings)
                    self.new_session.add(btc_settings)
                    logger.info(f"Created BTC settings for strategy {strategy.id}")
                
                elif strategy.strategy_type == StrategyTypeEnum.PORTFOLIO_DISTRIBUTOR:
                    # Check if already exists
                    existing = self.new_session.get(PortfolioDistributorSettings, strategy.id)
                    if existing:
                        logger.info(f"Portfolio settings already exist for strategy {strategy.id}")
                        continue
                    
                    # Filter and create portfolio settings
                    portfolio_fields = PortfolioDistributorSettings.model_fields.keys()
                    filtered_settings = {k: v for k, v in settings_dict.items() if k in portfolio_fields}
                    filtered_settings['strategy_id'] = strategy.id
                    
                    # Special handling for JSON fields
                    if 'symbols' in filtered_settings and isinstance(filtered_settings['symbols'], list):
                        filtered_settings['symbols'] = json.dumps(filtered_settings['symbols'])
                    if 'weights' in filtered_settings and isinstance(filtered_settings['weights'], dict):
                        filtered_settings['allocation_weights'] = json.dumps(filtered_settings['weights'])
                        del filtered_settings['weights']
                    
                    # Handle investment_frequency
                    if 'investment_frequency' in filtered_settings:
                        freq_value = filtered_settings['investment_frequency']
                        if isinstance(freq_value, str):
                            try:
                                filtered_settings['investment_frequency'] = InvestmentFrequencyEnum(freq_value)
                            except ValueError:
                                filtered_settings['investment_frequency'] = InvestmentFrequencyEnum.WEEKLY
                    
                    portfolio_settings = PortfolioDistributorSettings(**filtered_settings)
                    self.new_session.add(portfolio_settings)
                    logger.info(f"Created portfolio settings for strategy {strategy.id}")
            
            self.new_session.commit()
            logger.info("✅ Strategy settings migration completed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error migrating strategy settings: {e}")
            self.new_session.rollback()
            return False
    
    def run_full_migration(self) -> bool:
        """Run complete migration from legacy to SQLModel"""
        logger.info("🚀 Starting full migration to SQLModel...")
        
        # Initialize new database
        init_database()
        
        migrations = [
            ("Strategies", self.migrate_strategies),
            ("Positions", self.migrate_positions),
            ("Trades", self.migrate_trades),
            ("Performance Metrics", self.migrate_performance_metrics),
            ("Portfolios", self.migrate_portfolios),
            ("Event Logs", self.migrate_event_logs),  
            ("Strategy Settings", self.migrate_strategy_settings),
        ]
        
        for name, migration_func in migrations:
            logger.info(f"📦 Migrating {name}...")
            if not migration_func():
                logger.error(f"❌ Migration failed at {name}")
                return False
        
        logger.info("🎉 Full migration completed successfully!")
        return True

def main():
    """Main migration function"""
    logger.info("Starting SQLModel migration...")
    
    with SQLModelMigration() as migration:
        success = migration.run_full_migration()
        
        if success:
            logger.info("✅ Migration completed successfully!")
            logger.info("🔄 You can now update your application to use the SQLModel database")
            return 0
        else:
            logger.error("❌ Migration failed!")
            return 1

if __name__ == "__main__":
    sys.exit(main())