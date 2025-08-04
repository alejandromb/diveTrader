import asyncio
import threading
from typing import Dict, Optional
from sqlalchemy.orm import Session
from database.database import SessionLocal
from database.models import Strategy, StrategyType
from services.trading_service import TradingService
from services.performance_service import PerformanceService
from services.strategy_event_logger import strategy_event_logger
from strategies.btc_scalping.btc_scalping_strategy import BTCScalpingStrategy
from strategies.portfolio_distributor.portfolio_distributor_strategy import PortfolioDistributorStrategy
import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)

class StrategyRunner:
    def __init__(self):
        self.running_strategies: Dict[int, threading.Thread] = {}
        self.strategy_instances: Dict[int, object] = {}
        self.trading_service = TradingService()
        self.performance_service = PerformanceService()
        # Different check intervals for different strategy types
        self.check_intervals = {
            StrategyType.BTC_SCALPING: int(os.getenv("BTC_SCALPING_INTERVAL", 60)),  # 1 minute for scalping
            StrategyType.PORTFOLIO_DISTRIBUTOR: int(os.getenv("PORTFOLIO_INTERVAL", 3600))  # 1 hour for portfolio
        }
        self._shutdown = False
        
    def start_strategy(self, strategy_id: int) -> bool:
        """Start a trading strategy"""
        if strategy_id in self.running_strategies:
            logger.warning(f"Strategy {strategy_id} is already running")
            return False
            
        db = SessionLocal()
        try:
            strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
            if not strategy:
                logger.error(f"Strategy {strategy_id} not found")
                return False
                
            if not strategy.is_active:
                logger.error(f"Strategy {strategy_id} is not active")
                return False
                
            # Create strategy instance based on type
            strategy_instance = self._create_strategy_instance(strategy, db)
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
                name=f"Strategy-{strategy_id}"
            )
            
            # Mark as running before starting thread
            self.running_strategies[strategy_id] = thread
            thread.start()
            
            logger.info(f"Started strategy {strategy.name} (ID: {strategy_id})")
            # Log strategy start event
            with SessionLocal() as event_db:
                strategy_event_logger.log_strategy_start(event_db, strategy_id)
            return True
            
        except Exception as e:
            logger.error(f"Error starting strategy {strategy_id}: {e}")
            return False
        finally:
            db.close()
            
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
            with SessionLocal() as event_db:
                strategy_event_logger.log_strategy_stop(event_db, strategy_id)
            
            logger.info(f"Stopped strategy {strategy_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error stopping strategy {strategy_id}: {e}")
            return False
            
    def _create_strategy_instance(self, strategy: Strategy, db: Session):
        """Create strategy instance based on type"""
        try:
            if strategy.strategy_type == StrategyType.BTC_SCALPING:
                strategy_instance = BTCScalpingStrategy(
                    strategy_id=strategy.id,
                    trading_service=self.trading_service,
                    performance_service=self.performance_service,
                    db_session=db,
                    config=strategy.config
                )
                # Start the strategy instance
                strategy_instance.start()
                logger.info(f"Strategy instance created and started: {strategy_instance}")
                return strategy_instance
            elif strategy.strategy_type == StrategyType.PORTFOLIO_DISTRIBUTOR:
                strategy_instance = PortfolioDistributorStrategy(
                    trading_service=self.trading_service
                )
                # Initialize the strategy
                if strategy_instance.initialize_strategy(strategy, db):
                    logger.info(f"Portfolio distributor strategy instance created: {strategy_instance}")
                    return strategy_instance
                else:
                    logger.error(f"Failed to initialize portfolio distributor strategy {strategy.id}")
                    return None
            else:
                logger.error(f"Unknown strategy type: {strategy.strategy_type}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating strategy instance: {e}")
            return None
            
    def _run_strategy(self, strategy_id: int, strategy_instance, strategy_type: StrategyType):
        """Run strategy in a loop"""
        check_interval = self.check_intervals.get(strategy_type, 60)
        logger.info(f"Strategy {strategy_id} thread started (interval: {check_interval}s)")
        
        while not self._shutdown and strategy_id in self.running_strategies:
            try:
                # Create new DB session for each iteration
                db = SessionLocal()
                try:
                    # Check if strategy is still active in database
                    strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
                    
                    if not strategy or not strategy.is_active:
                        logger.info(f"Strategy {strategy_id} deactivated, stopping...")
                        break
                        
                    # Update strategy instance with fresh DB session
                    if hasattr(strategy_instance, 'db_session'):
                        strategy_instance.db_session = db
                        
                    # Run strategy iteration
                    if hasattr(strategy_instance, 'run_iteration'):
                        logger.info(f"Running iteration for strategy {strategy_id}")
                        
                        # Log trade check event
                        symbol = "BTC/USD" if strategy.strategy_type == StrategyType.BTC_SCALPING else "PORTFOLIO"
                        strategy_event_logger.log_trade_check(db, strategy_id, symbol, details={
                            "iteration_time": datetime.utcnow().isoformat(),
                            "check_interval": check_interval
                        })
                        
                        strategy_instance.run_iteration()
                        logger.info(f"Completed iteration for strategy {strategy_id}")
                        
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
                    self.performance_service.update_daily_performance(strategy_id, db)
                    
                    # Commit any changes
                    db.commit()
                    
                finally:
                    db.close()
                
                # Wait before next iteration
                import time
                time.sleep(check_interval)
                
            except Exception as e:
                logger.error(f"Error in strategy {strategy_id} loop: {e}")
                import time
                time.sleep(check_interval)
                
        logger.info(f"Strategy {strategy_id} thread stopped")
        
    def get_running_strategies(self) -> list:
        """Get list of currently running strategy IDs"""
        return list(self.running_strategies.keys())
        
    def is_strategy_running(self, strategy_id: int) -> bool:
        """Check if a strategy is currently running"""
        return strategy_id in self.running_strategies
        
    def shutdown(self):
        """Shutdown all running strategies"""
        self._shutdown = True
        logger.info("Shutting down strategy runner...")
        
        # Stop all strategies
        for strategy_id in list(self.running_strategies.keys()):
            self.stop_strategy(strategy_id)
            
        logger.info("Strategy runner shutdown complete")

# Global strategy runner instance
strategy_runner = StrategyRunner()