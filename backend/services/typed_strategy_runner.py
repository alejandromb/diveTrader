"""
Type-Safe Strategy Runner using SQLModel
Manages typed strategies with full validation and type safety
"""

import asyncio
import threading
from typing import Dict, Optional
from sqlmodel import Session, select
from database.sqlmodel_database import SessionLocal
from database.sqlmodel_models import Strategy, StrategyTypeEnum
from services.trading_service import TradingService
from services.performance_service import PerformanceService
from services.strategy_event_logger import strategy_event_logger
from services.account_sync_service import AccountSyncService
from strategies.btc_scalping.typed_btc_scalping_strategy import TypedBTCScalpingStrategy
from strategies.portfolio_distributor.typed_portfolio_distributor_strategy import TypedPortfolioDistributorStrategy
import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)

class TypedStrategyRunner:
    """Type-safe strategy runner using SQLModel"""
    
    def __init__(self):
        self.running_strategies: Dict[int, threading.Thread] = {}
        self.strategy_instances: Dict[int, object] = {}
        self.trading_service = TradingService()
        self.performance_service = PerformanceService()
        self.account_sync_service = AccountSyncService()
        
        # Different check intervals for different strategy types
        self.check_intervals = {
            StrategyTypeEnum.BTC_SCALPING: int(os.getenv("BTC_SCALPING_INTERVAL", 60)),  # 1 minute for scalping
            StrategyTypeEnum.PORTFOLIO_DISTRIBUTOR: int(os.getenv("PORTFOLIO_INTERVAL", 3600))  # 1 hour for portfolio
        }
        self._shutdown = False
        
        logger.info("✅ Typed Strategy Runner initialized")
        
    def start_strategy(self, strategy_id: int) -> bool:
        """Start a trading strategy with type safety"""
        if strategy_id in self.running_strategies:
            logger.warning(f"Strategy {strategy_id} is already running")
            return False
            
        with Session(SessionLocal().bind) as db:
            try:
                strategy = db.get(Strategy, strategy_id)
                if not strategy:
                    logger.error(f"Strategy {strategy_id} not found")
                    return False
                    
                if not strategy.is_active:
                    logger.error(f"Strategy {strategy_id} is not active")
                    return False

                # 🔄 AUTOMATIC ACCOUNT SYNC - Sync strategy capital with Alpaca account before starting
                logger.info(f"🔄 Syncing strategy {strategy_id} capital with Alpaca account...")
                sync_success = self.account_sync_service.sync_strategy_capital(strategy_id, db)
                if sync_success:
                    logger.info(f"✅ Strategy {strategy_id} capital synced with Alpaca account")
                    # Refresh strategy object to get updated capital
                    db.refresh(strategy)
                else:
                    logger.warning(f"⚠️ Could not sync strategy {strategy_id} capital with Alpaca account")
                    # Continue anyway - don't block strategy start due to sync failure
                    
                # Create typed strategy instance based on type
                strategy_instance = self._create_typed_strategy_instance(strategy, db)
                if not strategy_instance:
                    logger.error(f"Failed to create strategy instance for {strategy_id}")
                    return False
                    
                # Add to running strategies BEFORE starting thread to avoid race condition
                self.strategy_instances[strategy_id] = strategy_instance
                
                # Start strategy in separate thread
                thread = threading.Thread(
                    target=self._run_strategy,
                    args=(strategy_id, strategy_instance, strategy.strategy_type),
                    daemon=True,
                    name=f"TypedStrategy-{strategy_id}"
                )
                
                # Mark as running before starting thread
                self.running_strategies[strategy_id] = thread
                thread.start()
                
                logger.info(f"✅ Started typed strategy {strategy.name} (ID: {strategy_id})")
                # Log strategy start event
                with Session(SessionLocal().bind) as event_db:
                    strategy_event_logger.log_strategy_start(event_db, strategy_id)
                return True
                
            except Exception as e:
                logger.error(f"Error starting strategy {strategy_id}: {e}")
                return False
            
    def stop_strategy(self, strategy_id: int) -> bool:
        """Stop a running strategy"""
        if strategy_id not in self.running_strategies:
            logger.warning(f"Strategy {strategy_id} is not running")
            return False
            
        try:
            # Stop the strategy instance
            strategy_instance = self.strategy_instances.get(strategy_id)
            if strategy_instance and hasattr(strategy_instance, 'stop'):
                strategy_instance.stop()
                
            # Wait for thread to finish (with timeout)
            thread = self.running_strategies[strategy_id]
            thread.join(timeout=30)
            
            # Clean up
            del self.running_strategies[strategy_id]
            del self.strategy_instances[strategy_id]
            
            # Log strategy stop event
            with Session(SessionLocal().bind) as event_db:
                strategy_event_logger.log_strategy_stop(event_db, strategy_id)
            
            logger.info(f"✅ Stopped typed strategy {strategy_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error stopping strategy {strategy_id}: {e}")
            return False
            
    def _create_typed_strategy_instance(self, strategy: Strategy, db: Session):
        """Create typed strategy instance based on type"""
        try:
            if strategy.strategy_type == StrategyTypeEnum.BTC_SCALPING:
                strategy_instance = TypedBTCScalpingStrategy(
                    strategy_id=strategy.id,
                    trading_service=self.trading_service,
                    performance_service=self.performance_service,
                    db_session=db
                )
                # Start the strategy instance
                if strategy_instance.start():
                    logger.info(f"✅ Created typed BTC scalping strategy: {strategy_instance}")
                    return strategy_instance
                else:
                    logger.error(f"Failed to start BTC scalping strategy {strategy.id}")
                    return None
                    
            elif strategy.strategy_type == StrategyTypeEnum.PORTFOLIO_DISTRIBUTOR:
                strategy_instance = TypedPortfolioDistributorStrategy(
                    strategy_id=strategy.id,
                    trading_service=self.trading_service,
                    db_session=db
                )
                # Start the strategy instance
                if strategy_instance.start():
                    logger.info(f"✅ Created typed portfolio distributor strategy: {strategy_instance}")
                    return strategy_instance
                else:
                    logger.error(f"Failed to start portfolio distributor strategy {strategy.id}")
                    return None
            else:
                logger.error(f"Unknown strategy type: {strategy.strategy_type}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating typed strategy instance: {e}")
            return None
            
    def _run_strategy(self, strategy_id: int, strategy_instance, strategy_type: StrategyTypeEnum):
        """Run strategy in a loop with type safety"""
        check_interval = self.check_intervals.get(strategy_type, 60)
        logger.info(f"🚀 Typed strategy {strategy_id} thread started (interval: {check_interval}s)")
        
        # Track iterations for periodic account sync
        iteration_count = 0
        sync_frequency = 60  # Sync every 60 iterations
        
        while not self._shutdown and strategy_id in self.running_strategies:
            try:
                # Create new DB session for each iteration
                with Session(SessionLocal().bind) as db:
                    # Check if strategy is still active in database
                    strategy = db.get(Strategy, strategy_id)
                    
                    if not strategy or not strategy.is_active:
                        logger.info(f"Strategy {strategy_id} deactivated, stopping...")
                        break

                    # 🔄 PERIODIC ACCOUNT SYNC - Sync capital periodically during execution
                    iteration_count += 1
                    if iteration_count % sync_frequency == 0:
                        logger.info(f"🔄 Periodic account sync for strategy {strategy_id} (iteration {iteration_count})")
                        sync_success = self.account_sync_service.sync_strategy_capital(strategy_id, db)
                        if sync_success:
                            logger.info(f"✅ Strategy {strategy_id} capital synced during execution")
                            db.refresh(strategy)  # Refresh to get updated capital
                        else:
                            logger.warning(f"⚠️ Periodic account sync failed for strategy {strategy_id}")
                        
                        # Log account sync event
                        strategy_event_logger.log_account_sync(db, strategy_id, {
                            "iteration": iteration_count,
                            "sync_success": sync_success,
                            "capital": float(strategy.current_capital) if strategy else 0
                        })
                        
                    # Update strategy instance with fresh DB session
                    if hasattr(strategy_instance, 'db_session'):
                        strategy_instance.db_session = db
                        
                    # Run strategy iteration
                    if hasattr(strategy_instance, 'run_iteration'):
                        logger.debug(f"Running iteration for typed strategy {strategy_id}")
                        
                        # Log trade check event
                        symbol = "BTC/USD" if strategy.strategy_type == StrategyTypeEnum.BTC_SCALPING else "PORTFOLIO"
                        strategy_event_logger.log_trade_check(db, strategy_id, symbol, details={
                            "iteration_time": datetime.utcnow().isoformat(),
                            "check_interval": check_interval,
                            "strategy_type": strategy.strategy_type.value
                        })
                        
                        strategy_instance.run_iteration()
                        logger.debug(f"Completed iteration for typed strategy {strategy_id}")
                        
                        # Log performance update
                        try:
                            metrics = self.performance_service.calculate_strategy_performance(strategy_id, db)
                            if metrics:
                                strategy_event_logger.log_performance_update(db, strategy_id, {
                                    "roi": metrics.get("roi_percentage", 0),
                                    "pnl": metrics.get("total_pnl", 0),
                                    "total_trades": metrics.get("total_trades", 0)
                                })
                        except Exception as e:
                            logger.warning(f"Could not log performance update: {e}")
                        
                    # Update performance metrics
                    try:
                        self.performance_service.update_daily_performance(strategy_id, db)
                    except Exception as e:
                        logger.warning(f"Could not update performance metrics: {e}")
                    
                    # Commit any changes
                    db.commit()
                
                # Wait before next iteration
                import time
                time.sleep(check_interval)
                
            except Exception as e:
                logger.error(f"Error in typed strategy {strategy_id} loop: {e}")
                import time
                time.sleep(check_interval)
                
        logger.info(f"🛑 Typed strategy {strategy_id} thread stopped")
        
    def get_running_strategies(self) -> list:
        """Get list of currently running strategy IDs"""
        return list(self.running_strategies.keys())
        
    def is_strategy_running(self, strategy_id: int) -> bool:
        """Check if a strategy is currently running"""
        return strategy_id in self.running_strategies
        
    def get_strategy_status(self, strategy_id: int) -> dict:
        """Get detailed status of a strategy"""
        try:
            strategy_instance = self.strategy_instances.get(strategy_id)
            if strategy_instance and hasattr(strategy_instance, 'get_status'):
                return strategy_instance.get_status()
            else:
                return {
                    "strategy_id": strategy_id,
                    "is_running": self.is_strategy_running(strategy_id),
                    "error": "Strategy instance not found or no status method"
                }
        except Exception as e:
            return {
                "strategy_id": strategy_id,
                "error": f"Error getting status: {e}"
            }
        
    def shutdown(self):
        """Shutdown all running strategies"""
        self._shutdown = True
        logger.info("🛑 Shutting down typed strategy runner...")
        
        # Stop all strategies
        for strategy_id in list(self.running_strategies.keys()):
            self.stop_strategy(strategy_id)
            
        logger.info("✅ Typed strategy runner shutdown complete")

# Global typed strategy runner instance
typed_strategy_runner = TypedStrategyRunner()