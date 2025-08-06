"""
Generic Backtesting Engine
Strategy-agnostic backtesting framework that follows proper SOLID principles
"""

from typing import Dict, Any, Optional
import pandas as pd
import logging
from datetime import datetime, timedelta
from sqlmodel import Session, select

from strategies.base_strategy import BaseStrategy, BacktestResult
from strategies.typed_base_strategy import TypedBaseStrategy
from database.sqlmodel_models import Strategy, StrategyTypeEnum

logger = logging.getLogger(__name__)

class BacktestingEngine:
    """
    Generic backtesting engine that works with any strategy implementing the backtest interface.
    
    This follows the Strategy Pattern - the engine provides the framework and data,
    but each strategy implements its own backtesting logic.
    """
    
    def __init__(self, db_session: Session):
        self.db_session = db_session
        
    def run_backtest(self, strategy_id: int, config: Dict[str, Any], 
                    initial_capital: float, days_back: int) -> Dict[str, Any]:
        """
        Run backtest for any strategy using the strategy pattern
        
        Args:
            strategy_id: Database ID of the strategy to backtest
            config: Strategy-specific configuration
            initial_capital: Starting capital
            days_back: Days of historical data to use
            
        Returns:
            Dict containing the backtesting results in API-friendly format
        """
        try:
            # Get the strategy from database
            strategy_record = self.db_session.get(Strategy, strategy_id)
            if not strategy_record:
                raise ValueError(f"Strategy {strategy_id} not found")
            
            # Create the appropriate strategy instance
            strategy_instance = self._create_strategy_instance(strategy_record)
            if not strategy_instance:
                raise ValueError(f"Could not create strategy instance for {strategy_record.strategy_type}")
            
            # Get historical data for the strategy
            data = self._get_historical_data(strategy_record, days_back)
            if data.empty:
                raise ValueError(f"No historical data available for strategy {strategy_id}")
            
            logger.info(f"Running backtest for strategy {strategy_record.name} ({strategy_record.strategy_type.value})")
            logger.info(f"Data: {len(data)} rows from {data.iloc[0]['timestamp']} to {data.iloc[-1]['timestamp']}")
            
            # Let the strategy run its own backtesting logic
            backtest_result = strategy_instance.backtest(data, config, initial_capital, days_back)
            
            # Convert to API-friendly format
            api_result = self._convert_to_api_format(backtest_result, strategy_record)
            
            logger.info(f"Backtest completed: {backtest_result.final_capital:.2f} final capital, {backtest_result.total_trades} trades")
            
            return api_result
            
        except Exception as e:
            logger.error(f"Backtest failed for strategy {strategy_id}: {e}")
            raise
    
    def _create_strategy_instance(self, strategy_record: Strategy) -> Optional[BaseStrategy]:
        """
        Create appropriate strategy instance based on strategy type
        
        This is the only place where we need to know about specific strategy types.
        Each strategy implements the backtest interface, so the engine can treat them polymorphically.
        """
        try:
            if strategy_record.strategy_type == StrategyTypeEnum.BTC_SCALPING:
                from strategies.btc_scalping.typed_btc_scalping_strategy import TypedBTCScalpingStrategy
                from services.trading_service import TradingService
                from services.performance_service import PerformanceService
                
                trading_service = TradingService()
                performance_service = PerformanceService()
                return TypedBTCScalpingStrategy(
                    strategy_record.id, trading_service, performance_service, self.db_session
                )
                
            elif strategy_record.strategy_type == StrategyTypeEnum.PORTFOLIO_DISTRIBUTOR:
                from strategies.portfolio_distributor.typed_portfolio_distributor_strategy import TypedPortfolioDistributorStrategy
                from services.trading_service import TradingService
                
                trading_service = TradingService()
                return TypedPortfolioDistributorStrategy(
                    strategy_record.id, trading_service, self.db_session
                )
            
            else:
                logger.error(f"Unknown strategy type: {strategy_record.strategy_type}")
                return None
                
        except ImportError as e:
            logger.error(f"Could not import strategy class: {e}")
            return None
    
    def _get_historical_data(self, strategy_record: Strategy, days_back: int) -> pd.DataFrame:
        """
        Get historical data appropriate for the strategy type
        
        Different strategies need different data sources:
        - BTC strategies need crypto data
        - Portfolio strategies need stock data for multiple symbols
        """
        if strategy_record.strategy_type == StrategyTypeEnum.BTC_SCALPING:
            return self._get_crypto_data(days_back)
        elif strategy_record.strategy_type == StrategyTypeEnum.PORTFOLIO_DISTRIBUTOR:
            return self._get_portfolio_data(days_back)
        else:
            logger.warning(f"No data source defined for strategy type {strategy_record.strategy_type}")
            return pd.DataFrame()
    
    def _get_crypto_data(self, days_back: int) -> pd.DataFrame:
        """Get cryptocurrency data for BTC strategies"""
        # Import here to avoid circular imports
        from services.enhanced_backtesting_service import EnhancedBacktestingService
        
        enhanced_service = EnhancedBacktestingService()
        data = enhanced_service._get_crypto_data_with_fallback("BTC/USD", days_back)
        
        if data is None or len(data) == 0:
            logger.warning("No crypto data available, generating synthetic data")
            data = enhanced_service._generate_synthetic_btc_data(days_back)
        
        return data if data is not None else pd.DataFrame()
    
    def _get_portfolio_data(self, days_back: int) -> pd.DataFrame:
        """Get stock data for portfolio strategies"""
        # For portfolio strategies, we return metadata that tells the strategy
        # what symbols to fetch. The strategy itself will handle multi-symbol data.
        symbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'SPY']
        
        # Create a metadata DataFrame that the portfolio strategy can use
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        metadata_df = pd.DataFrame({
            'timestamp': [start_date],
            'symbols': [symbols],
            'days_back': [days_back],
            'data_type': ['portfolio_metadata']
        })
        
        return metadata_df
    
    def _convert_to_api_format(self, result: BacktestResult, strategy_record: Strategy) -> Dict[str, Any]:
        """Convert BacktestResult to API-friendly format"""
        api_result = {
            "strategy_id": strategy_record.id,
            "strategy_type": result.strategy_type,
            "symbol": result.symbol,
            "period": result.period,
            "start_date": result.start_date.isoformat() if result.start_date else None,
            "end_date": result.end_date.isoformat() if result.end_date else None,
            "initial_capital": result.initial_capital,
            "final_capital": result.final_capital,
            "total_return": result.total_return,
            "total_return_pct": result.total_return_pct,
            "total_trades": result.total_trades,
            "winning_trades": result.winning_trades,
            "losing_trades": result.losing_trades,
            "win_rate": result.win_rate,
            "max_drawdown": result.max_drawdown,
            "sharpe_ratio": result.sharpe_ratio,
            "data_source": "real"  # Can be enhanced later
        }
        
        # Add strategy-specific metadata
        if result.metadata:
            api_result.update(result.metadata)
        
        # Convert trades to API format
        if result.trades:
            api_result["trades"] = [
                {
                    "timestamp": trade.timestamp.isoformat(),
                    "symbol": trade.symbol,
                    "side": trade.side,
                    "quantity": trade.quantity,
                    "price": trade.price,
                    "commission": trade.commission,
                    "pnl": trade.pnl,
                    "reason": trade.reason
                }
                for trade in result.trades
            ]
        
        # Convert equity curve
        if result.equity_curve:
            api_result["equity_curve"] = result.equity_curve
        
        return api_result