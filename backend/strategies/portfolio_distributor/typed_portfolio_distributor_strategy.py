"""
Type-Safe Portfolio Distributor Strategy using SQLModel
Full type safety with automatic validation and IDE support
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from sqlmodel import Session, select
from database.sqlmodel_models import (
    Strategy, Position, Trade, Portfolio, PortfolioDistributorSettings,
    InvestmentFrequencyEnum
)
from services.trading_service import TradingService
from strategies.typed_base_strategy import TypedBaseStrategy
from alpaca.trading.enums import OrderSide

logger = logging.getLogger(__name__)

class TypedPortfolioDistributorStrategy(TypedBaseStrategy):
    """Type-safe Portfolio Distributor Strategy with SQLModel validation"""

    def __init__(self, strategy_id: int, trading_service: TradingService, db_session: Session):
        super().__init__(strategy_id, db_session)
        self.trading_service = trading_service
        self.is_running = False
        
        logger.info(f"Typed Portfolio Distributor Strategy initialized for strategy {strategy_id}")
    
    @property
    def portfolio_settings(self) -> Optional[PortfolioDistributorSettings]:
        """Get typed portfolio distributor settings"""
        return self.settings if isinstance(self.settings, PortfolioDistributorSettings) else None

    def start(self) -> bool:
        """Start the strategy with validation"""
        try:
            is_valid, error = self.validate_settings()
            if not is_valid:
                logger.error(f"Strategy {self.strategy_id} has invalid settings: {error}")
                return False
            
            if not self.portfolio_settings:
                logger.error(f"No portfolio settings found for strategy {self.strategy_id}")
                return False
                
            # Create or update portfolio record
            self._create_portfolio_record()
            
            self.is_running = True
            logger.info(f"✅ Typed Portfolio Distributor Strategy {self.strategy_id} started")
            logger.info(f"Settings: investment_amount=${self.portfolio_settings.investment_amount}, "
                       f"frequency={self.portfolio_settings.investment_frequency.value}, "
                       f"symbols={len(self.portfolio_settings.symbols_list)}")
            return True
        except Exception as e:
            logger.error(f"Error starting strategy {self.strategy_id}: {e}")
            return False

    def stop(self) -> bool:
        """Stop the strategy"""
        try:
            self.is_running = False
            logger.info(f"✅ Typed Portfolio Distributor Strategy {self.strategy_id} stopped")
            return True
        except Exception as e:
            logger.error(f"Error stopping strategy {self.strategy_id}: {e}")
            return False

    def run_iteration(self):
        """Single iteration of the strategy - called by strategy runner"""
        if not self.is_running or not self.portfolio_settings:
            return
            
        try:
            result = self.run_strategy()
            logger.info(f"Portfolio distributor iteration completed: {result}")
            return result
        except Exception as e:
            logger.error(f"Error in portfolio distributor iteration: {e}")
            return None
    
    def _create_portfolio_record(self) -> bool:
        """Create or update portfolio record using typed settings"""
        try:
            if not self.strategy or not self.portfolio_settings:
                return False
                
            # Check if portfolio already exists
            statement = select(Portfolio).where(Portfolio.strategy_id == self.strategy_id)
            portfolio = self.db_session.exec(statement).first()
            
            if portfolio:
                # Update existing portfolio
                portfolio.symbols = self.portfolio_settings.symbols
                portfolio.allocation_weights = self.portfolio_settings.allocation_weights
                portfolio.investment_amount = self.portfolio_settings.investment_amount
                portfolio.investment_frequency = self.portfolio_settings.investment_frequency
            else:
                # Create new portfolio
                portfolio = Portfolio(
                    strategy_id=self.strategy_id,
                    name=f"{self.strategy.name} Portfolio",
                    symbols=self.portfolio_settings.symbols,
                    allocation_weights=self.portfolio_settings.allocation_weights,
                    investment_frequency=self.portfolio_settings.investment_frequency,
                    investment_amount=self.portfolio_settings.investment_amount,
                    next_investment_date=self._calculate_next_investment_date()
                )
                self.db_session.add(portfolio)
            
            self.db_session.commit()
            logger.info(f"Portfolio record created/updated for strategy {self.strategy_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating portfolio record: {e}")
            return False
    
    def _calculate_next_investment_date(self) -> datetime:
        """Calculate the next investment date based on frequency"""
        if not self.portfolio_settings:
            return datetime.utcnow() + timedelta(days=7)
        
        now = datetime.utcnow()
        frequency = self.portfolio_settings.investment_frequency
        
        if frequency == InvestmentFrequencyEnum.DAILY:
            return now + timedelta(days=1)
        elif frequency == InvestmentFrequencyEnum.WEEKLY:
            # Next Monday
            days_ahead = 0 - now.weekday()  # Monday is 0
            if days_ahead <= 0:  # Target day already happened this week
                days_ahead += 7
            return now + timedelta(days=days_ahead)
        elif frequency == InvestmentFrequencyEnum.BIWEEKLY:
            return now + timedelta(days=14)
        elif frequency == InvestmentFrequencyEnum.MONTHLY:
            # First day of next month
            if now.month == 12:
                return datetime(now.year + 1, 1, 1)
            else:
                return datetime(now.year, now.month + 1, 1)
        else:
            # Default to weekly
            return now + timedelta(days=7)
    
    def should_invest_today(self) -> bool:
        """Check if we should make an investment today using typed settings"""
        try:
            statement = select(Portfolio).where(Portfolio.strategy_id == self.strategy_id)
            portfolio = self.db_session.exec(statement).first()
            
            if not portfolio:
                return False
                
            now = datetime.utcnow()
            return now >= portfolio.next_investment_date
            
        except Exception as e:
            logger.error(f"Error checking investment schedule: {e}")
            return False
    
    def execute_investment(self) -> bool:
        """Execute scheduled investment using typed settings"""
        try:
            if not self.portfolio_settings or not self.strategy:
                logger.error(f"Missing settings or strategy for {self.strategy_id}")
                return False
            
            statement = select(Portfolio).where(Portfolio.strategy_id == self.strategy_id)
            portfolio = self.db_session.exec(statement).first()
            
            if not portfolio:
                logger.error(f"No portfolio found for strategy {self.strategy_id}")
                return False
            
            # Calculate investment amounts per symbol using typed settings
            total_investment = min(self.portfolio_settings.investment_amount, self.strategy.current_capital)
            
            if total_investment < 10:  # Minimum investment
                logger.warning(f"Insufficient capital for investment: ${total_investment}")
                return False
            
            investment_results = []
            symbols = self.portfolio_settings.symbols_list
            weights = self.portfolio_settings.weights_dict
            
            # Execute trades for each symbol
            for symbol in symbols:
                weight = weights.get(symbol, 1.0 / len(symbols))  # Equal weight if not specified
                investment_amount = total_investment * (weight / 100.0)  # Convert percentage to decimal
                
                if investment_amount < 1:  # Skip very small amounts
                    continue
                
                try:
                    # Get current price to calculate quantity
                    quotes = self.trading_service.get_latest_quotes([symbol])
                    current_price = quotes.get(symbol, {}).get('price', 0)
                    
                    if current_price > 0:
                        quantity = int(investment_amount / current_price)  # Buy whole shares only
                        
                        if quantity > 0:
                            # Place buy order
                            trade = self.trading_service.place_order(
                                strategy_id=self.strategy_id,
                                symbol=symbol,
                                side=OrderSide.BUY,
                                quantity=quantity,
                                db=self.db_session
                            )
                            
                            investment_results.append({
                                'symbol': symbol,
                                'quantity': quantity,
                                'estimated_cost': quantity * current_price,
                                'trade_id': trade.id
                            })
                            
                            logger.info(f"Invested in {symbol}: {quantity} shares @ ${current_price:.2f}")
                        
                except Exception as e:
                    logger.error(f"Error investing in {symbol}: {e}")
                    continue
            
            # Update next investment date
            portfolio.next_investment_date = self._calculate_next_investment_date()
            self.db_session.commit()
            
            if investment_results:
                total_invested = sum(result['estimated_cost'] for result in investment_results)
                logger.info(f"Portfolio investment completed: ${total_invested:.2f} across {len(investment_results)} symbols")
                return True
            else:
                logger.warning("No investments were made")
                return False
                
        except Exception as e:
            logger.error(f"Error executing investment: {e}")
            return False
    
    def check_rebalancing_needed(self) -> bool:
        """Check if portfolio needs rebalancing using typed settings"""
        try:
            if not self.portfolio_settings:
                return False
            
            # Get current positions
            statement = select(Position).where(Position.strategy_id == self.strategy_id)
            positions = self.db_session.exec(statement).all()
            
            if len(positions) < 2:  # Need at least 2 positions to rebalance
                return False
            
            # Calculate current allocation
            total_value = sum(pos.market_value for pos in positions)
            current_allocations = {}
            
            for pos in positions:
                current_allocations[pos.symbol] = (pos.market_value / total_value) * 100
            
            # Compare with target allocations using typed settings
            target_allocations = self.portfolio_settings.weights_dict
            
            # Check if any allocation is off by more than threshold
            for symbol, target_weight in target_allocations.items():
                current_weight = current_allocations.get(symbol, 0)
                deviation = abs(current_weight - target_weight)
                
                if deviation > self.portfolio_settings.rebalance_threshold:
                    logger.info(f"Rebalancing needed: {symbol} is {deviation:.1f}% off target")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking rebalancing: {e}")
            return False
    
    def run_strategy(self) -> Dict:
        """Main strategy execution loop using typed settings"""
        try:
            result = {
                'strategy_id': self.strategy_id,
                'timestamp': datetime.utcnow().isoformat(),
                'actions_taken': [],
                'status': 'success'
            }
            
            # Check if it's time to invest
            if self.should_invest_today():
                investment_success = self.execute_investment()
                result['actions_taken'].append({
                    'type': 'investment',
                    'success': investment_success
                })
            
            # Check if rebalancing is needed (run less frequently)
            now = datetime.utcnow()
            if now.hour == 16 and now.minute < 5:  # Check at market close
                if self.check_rebalancing_needed():
                    result['actions_taken'].append({
                        'type': 'rebalancing_check',
                        'rebalancing_needed': True
                    })
                    # Note: Actual rebalancing implementation would go here
            
            return result
            
        except Exception as e:
            logger.error(f"Error running portfolio distributor strategy: {e}")
            return {
                'strategy_id': self.strategy_id,
                'timestamp': datetime.utcnow().isoformat(),
                'status': 'error',
                'error': str(e)
            }
    
    def get_status(self) -> dict:
        """Get strategy status with typed settings"""
        if not self.strategy or not self.portfolio_settings:
            return {"error": "Strategy or settings not loaded"}
        
        return {
            "strategy_id": self.strategy_id,
            "is_running": self.is_running,
            "settings": self.get_settings_dict(),
            "symbols": self.portfolio_settings.symbols_list,
            "weights": self.portfolio_settings.weights_dict,
            "investment_amount": self.portfolio_settings.investment_amount,
            "investment_frequency": self.portfolio_settings.investment_frequency.value,
            "rebalance_threshold": self.portfolio_settings.rebalance_threshold
        }