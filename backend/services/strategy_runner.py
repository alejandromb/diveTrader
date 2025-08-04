import asyncio
import threading
from typing import Dict, Optional
from sqlalchemy.orm import Session
from database.database import SessionLocal
from database.models import Strategy, StrategyType
from services.trading_service import TradingService
from services.performance_service import PerformanceService
from strategies.btc_scalping_strategy import BTCScalpingStrategy
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
        self.check_interval = int(os.getenv("STRATEGY_CHECK_INTERVAL", 60))
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
                
            # Start strategy in separate thread
            thread = threading.Thread(
                target=self._run_strategy,
                args=(strategy_id, strategy_instance),
                daemon=True,
                name=f"Strategy-{strategy_id}"
            )
            thread.start()
            
            self.running_strategies[strategy_id] = thread
            self.strategy_instances[strategy_id] = strategy_instance
            
            logger.info(f"Started strategy {strategy.name} (ID: {strategy_id})")
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
                # TODO: Implement portfolio distributor
                logger.warning("Portfolio distributor strategy not implemented yet")
                return None
            else:
                logger.error(f"Unknown strategy type: {strategy.strategy_type}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating strategy instance: {e}")
            return None
            
    def _run_strategy(self, strategy_id: int, strategy_instance):
        """Run strategy in a loop"""
        logger.info(f"Strategy {strategy_id} thread started")
        
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
                    strategy_instance.db_session = db
                        
                    # Run strategy iteration
                    if hasattr(strategy_instance, 'run_iteration'):
                        logger.info(f"Running iteration for strategy {strategy_id}")
                        strategy_instance.run_iteration()
                        logger.info(f"Completed iteration for strategy {strategy_id}")
                        
                    # Update performance metrics
                    self.performance_service.update_daily_performance(strategy_id, db)
                    
                    # Commit any changes
                    db.commit()
                    
                finally:
                    db.close()
                
                # Wait before next iteration
                import time
                time.sleep(self.check_interval)
                
            except Exception as e:
                logger.error(f"Error in strategy {strategy_id} loop: {e}")
                import time
                time.sleep(self.check_interval)
                
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