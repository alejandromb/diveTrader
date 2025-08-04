import os
import logging
from typing import Optional
from sqlalchemy.orm import Session
from alpaca.trading.client import TradingClient
from alpaca.trading.enums import AccountStatus
from database.models import Strategy

logger = logging.getLogger(__name__)

class AccountSyncService:
    def __init__(self):
        self.trading_client = TradingClient(
            api_key=os.getenv("ALPACA_API_KEY"),
            secret_key=os.getenv("ALPACA_SECRET_KEY"),
            paper=True
        )
        
    def get_account_info(self) -> Optional[dict]:
        """Get current Alpaca account information"""
        try:
            account = self.trading_client.get_account()
            logger.info(f"Account attributes: {[attr for attr in dir(account) if not attr.startswith('_')]}")
            return {
                "equity": float(account.equity),
                "cash": float(account.cash),
                "buying_power": float(account.buying_power),
                "portfolio_value": float(getattr(account, 'portfolio_value', account.equity)),
                "status": str(account.status),
                "account_id": account.id,
                "account_number": getattr(account, 'account_number', 'N/A')
            }
        except Exception as e:
            logger.error(f"Error getting account info: {e}")
            return None
    
    def sync_strategy_capital(self, strategy_id: int, db: Session) -> bool:
        """Sync strategy capital with Alpaca account"""
        try:
            account_info = self.get_account_info()
            if not account_info:
                return False
                
            strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
            if not strategy:
                logger.error(f"Strategy {strategy_id} not found")
                return False
                
            # Update strategy capital to match account equity
            old_capital = strategy.current_capital
            strategy.current_capital = account_info["equity"]
            strategy.initial_capital = account_info["equity"]
            
            db.commit()
            
            logger.info(f"Updated strategy {strategy_id} capital from ${old_capital:.2f} to ${account_info['equity']:.2f}")
            return True
            
        except Exception as e:
            logger.error(f"Error syncing strategy capital: {e}")
            return False
    
    def get_positions(self) -> list:
        """Get current positions from Alpaca"""
        try:
            positions = self.trading_client.get_all_positions()
            return [
                {
                    "symbol": pos.symbol,
                    "quantity": float(pos.qty),
                    "market_value": float(pos.market_value),
                    "cost_basis": float(pos.cost_basis),
                    "unrealized_pl": float(pos.unrealized_pl),
                    "unrealized_plpc": float(pos.unrealized_plpc),
                    "side": pos.side
                }
                for pos in positions
            ]
        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            return []
    
    def get_orders(self, status="all") -> list:
        """Get orders from Alpaca"""
        try:
            orders = self.trading_client.get_orders(status=status)
            return [
                {
                    "id": order.id,
                    "symbol": order.symbol,
                    "quantity": float(order.qty),
                    "side": order.side,
                    "order_type": order.order_type,
                    "status": order.status,
                    "filled_qty": float(order.filled_qty or 0),
                    "filled_avg_price": float(order.filled_avg_price or 0),
                    "created_at": order.created_at,
                    "updated_at": order.updated_at
                }
                for order in orders
            ]
        except Exception as e:
            logger.error(f"Error getting orders: {e}")
            return []