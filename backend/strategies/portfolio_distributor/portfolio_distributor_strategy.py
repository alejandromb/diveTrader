import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from database.models import Strategy, Position, Trade, Portfolio
from services.trading_service import TradingService
from strategies.base_strategy import BaseStrategy
from services.strategy_settings_service import SettingType
from alpaca.trading.enums import OrderSide
from config.constants import DEFAULT_PORTFOLIO_SYMBOLS, DEFAULT_PORTFOLIO_WEIGHTS

logger = logging.getLogger(__name__)

class PortfolioDistributorStrategy(BaseStrategy):
    def __init__(self, strategy_id: int, trading_service: TradingService, db_session: Session):
        super().__init__(strategy_id, db_session)
        self.trading_service = trading_service
        self.logger = logging.getLogger(__name__)
        self.is_running = False
        
        # Initialize default settings if not already present
        if not self.get_setting("investment_amount"):
            self.initialize_default_settings("portfolio_distributor")
            logger.info("Initialized default settings for portfolio distributor strategy")
        
    def start(self) -> bool:
        """Start the strategy"""
        try:
            if not self.validate_settings():
                logger.error(f"Strategy {self.strategy_id} has invalid settings")
                return False
                
            # Create or update portfolio record
            self._create_portfolio_record()
            
            self.is_running = True
            logger.info(f"Portfolio Distributor Strategy {self.strategy_id} started")
            return True
        except Exception as e:
            logger.error(f"Error starting strategy {self.strategy_id}: {e}")
            return False
    
    def stop(self) -> bool:
        """Stop the strategy"""
        try:
            self.is_running = False
            logger.info(f"Portfolio Distributor Strategy {self.strategy_id} stopped")
            return True
        except Exception as e:
            logger.error(f"Error stopping strategy {self.strategy_id}: {e}")
            return False
    
    def _create_portfolio_record(self) -> bool:
        """Create or update portfolio record using settings"""
        try:
            strategy = self.db_session.query(Strategy).filter(Strategy.id == self.strategy_id).first()
            if not strategy:
                return False
                
            # Check if portfolio already exists
            portfolio = self.db_session.query(Portfolio).filter(
                Portfolio.strategy_id == self.strategy_id
            ).first()
            
            symbols = self.get_list_setting("symbols", DEFAULT_PORTFOLIO_SYMBOLS)
            weights = self.get_dict_setting("weights", DEFAULT_PORTFOLIO_WEIGHTS)
            investment_amount = self.get_float_setting("investment_amount", 1000.0)
            investment_frequency = "weekly"  # Fixed for now
            
            if portfolio:
                # Update existing portfolio
                portfolio.symbols = json.dumps(symbols)
                portfolio.allocation_weights = json.dumps(weights)
                portfolio.investment_amount = investment_amount
            else:
                # Create new portfolio
                portfolio = Portfolio(
                    strategy_id=self.strategy_id,
                    name=f"{strategy.name} Portfolio",
                    symbols=json.dumps(symbols),
                    allocation_weights=json.dumps(weights),
                    investment_frequency=investment_frequency,
                    investment_amount=investment_amount,
                    next_investment_date=self._calculate_next_investment_date(investment_frequency)
                )
                self.db_session.add(portfolio)
            
            self.db_session.commit()
            logger.info(f"Portfolio record created/updated for strategy {self.strategy_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating portfolio record: {e}")
            return False
    
    def _calculate_next_investment_date(self, frequency: str) -> datetime:
        """Calculate the next investment date based on frequency"""
        now = datetime.utcnow()
        
        if frequency == 'weekly':
            # Next Monday
            days_ahead = 0 - now.weekday()  # Monday is 0
            if days_ahead <= 0:  # Target day already happened this week
                days_ahead += 7
            return now + timedelta(days=days_ahead)
        
        elif frequency == 'monthly':
            # First day of next month
            if now.month == 12:
                return datetime(now.year + 1, 1, 1)
            else:
                return datetime(now.year, now.month + 1, 1)
        
        else:
            # Default to weekly
            return now + timedelta(days=7)
    
    def initialize_strategy(self, strategy: Strategy, db: Session) -> bool:
        """Legacy method for compatibility with strategy runner"""
        # This method is kept for compatibility but the actual initialization
        # is now done in __init__ and start() methods
        return True
    
    def should_invest_today(self, strategy_id: int, db: Session) -> bool:
        """Check if we should make an investment today"""
        try:
            portfolio = db.query(Portfolio).filter(
                Portfolio.strategy_id == strategy_id
            ).first()
            
            if not portfolio:
                return False
                
            now = datetime.utcnow()
            return now >= portfolio.next_investment_date
            
        except Exception as e:
            self.logger.error(f"Error checking investment schedule: {e}")
            return False
    
    def execute_investment(self, strategy_id: int, db: Session) -> bool:
        """Execute scheduled investment"""
        try:
            portfolio = db.query(Portfolio).filter(
                Portfolio.strategy_id == strategy_id
            ).first()
            
            if not portfolio:
                self.logger.error(f"No portfolio found for strategy {strategy_id}")
                return False
            
            strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
            if not strategy:
                return False
            
            # Parse configuration
            symbols = json.loads(portfolio.symbols)
            allocation_weights = json.loads(portfolio.allocation_weights)
            
            # Calculate investment amounts per symbol using settings
            investment_amount = self.get_float_setting("investment_amount", 1000.0)
            total_investment = min(investment_amount, strategy.current_capital)
            
            if total_investment < 10:  # Minimum investment
                self.logger.warning(f"Insufficient capital for investment: ${total_investment}")
                return False
            
            investment_results = []
            
            # Execute trades for each symbol
            for symbol in symbols:
                weight = allocation_weights.get(symbol, 1.0 / len(symbols))  # Equal weight if not specified
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
                                strategy_id=strategy_id,
                                symbol=symbol,
                                side=OrderSide.BUY,
                                quantity=quantity,
                                db=db
                            )
                            
                            investment_results.append({
                                'symbol': symbol,
                                'quantity': quantity,
                                'estimated_cost': quantity * current_price,
                                'trade_id': trade.id
                            })
                            
                            self.logger.info(f"Invested in {symbol}: {quantity} shares @ ${current_price:.2f}")
                        
                except Exception as e:
                    self.logger.error(f"Error investing in {symbol}: {e}")
                    continue
            
            # Update next investment date
            portfolio.next_investment_date = self._calculate_next_investment_date(
                portfolio.investment_frequency
            )
            db.commit()
            
            if investment_results:
                total_invested = sum(result['estimated_cost'] for result in investment_results)
                
                # Update strategy's total_invested amount
                try:
                    strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
                    if strategy:
                        strategy.total_invested = (strategy.total_invested or 0.0) + total_invested
                        db.commit()
                        self.logger.info(f"Updated strategy total_invested to ${strategy.total_invested:.2f}")
                except Exception as e:
                    self.logger.error(f"Error updating strategy total_invested: {e}")
                
                self.logger.info(f"Portfolio investment completed: ${total_invested:.2f} across {len(investment_results)} symbols")
                return True
            else:
                self.logger.warning("No investments were made")
                return False
                
        except Exception as e:
            self.logger.error(f"Error executing investment: {e}")
            return False
    
    def check_rebalancing_needed(self, strategy_id: int, db: Session) -> bool:
        """Check if portfolio needs rebalancing"""
        try:
            portfolio = db.query(Portfolio).filter(
                Portfolio.strategy_id == strategy_id
            ).first()
            
            if not portfolio:
                return False
            
            # Get current positions
            positions = db.query(Position).filter(
                Position.strategy_id == strategy_id
            ).all()
            
            if len(positions) < 2:  # Need at least 2 positions to rebalance
                return False
            
            # Calculate current allocation
            total_value = sum(pos.market_value for pos in positions)
            current_allocations = {}
            
            for pos in positions:
                current_allocations[pos.symbol] = (pos.market_value / total_value) * 100
            
            # Compare with target allocations using settings
            target_allocations = self.get_dict_setting("weights", {})
            rebalance_threshold = self.get_float_setting("rebalance_threshold", 5.0)
            
            # Check if any allocation is off by more than threshold
            for symbol, target_weight in target_allocations.items():
                current_weight = current_allocations.get(symbol, 0)
                deviation = abs(current_weight - target_weight)
                
                if deviation > rebalance_threshold:
                    self.logger.info(f"Rebalancing needed: {symbol} is {deviation:.1f}% off target")
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking rebalancing: {e}")
            return False
    
    def run_strategy(self, strategy_id: int, db: Session) -> Dict:
        """Main strategy execution loop"""
        try:
            result = {
                'strategy_id': strategy_id,
                'timestamp': datetime.utcnow().isoformat(),
                'actions_taken': [],
                'status': 'success'
            }
            
            # Check if it's time to invest
            if self.should_invest_today(strategy_id, db):
                investment_success = self.execute_investment(strategy_id, db)
                result['actions_taken'].append({
                    'type': 'investment',
                    'success': investment_success
                })
            
            # Check if rebalancing is needed (run less frequently)
            now = datetime.utcnow()
            if now.hour == 16 and now.minute < 5:  # Check at market close
                if self.check_rebalancing_needed(strategy_id, db):
                    result['actions_taken'].append({
                        'type': 'rebalancing_check',
                        'rebalancing_needed': True
                    })
                    # Note: Actual rebalancing implementation would go here
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error running portfolio distributor strategy: {e}")
            return {
                'strategy_id': strategy_id,
                'timestamp': datetime.utcnow().isoformat(),
                'status': 'error',
                'error': str(e)
            }
    
    def run_iteration(self):
        """Single iteration of the strategy - called by strategy runner"""
        if not self.is_running:
            return
            
        try:
            result = self.run_strategy(self.strategy_id, self.db_session)
            self.logger.info(f"Portfolio distributor iteration completed: {result}")
            return result
        except Exception as e:
            self.logger.error(f"Error in portfolio distributor iteration: {e}")
            return None
    
    def validate_settings(self) -> bool:
        """Validate strategy settings"""
        try:
            # Check required settings exist and are valid
            investment_amount = self.get_float_setting("investment_amount", 1000.0)
            if investment_amount <= 0:
                logger.error(f"Invalid investment_amount: {investment_amount}")
                return False
                
            symbols = self.get_list_setting("symbols", [])
            if not symbols or len(symbols) == 0:
                logger.error("No symbols configured for portfolio")
                return False
                
            weights = self.get_dict_setting("weights", {})
            if not weights:
                logger.error("No allocation weights configured")
                return False
                
            # Check that weights sum to approximately 100%
            total_weight = sum(weights.values())
            if abs(total_weight - 100.0) > 1.0:  # Allow 1% tolerance
                logger.error(f"Allocation weights sum to {total_weight}%, should be 100%")
                return False
                
            return True
        except Exception as e:
            logger.error(f"Error validating settings: {e}")
            return False