from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient, CryptoHistoricalDataClient
from alpaca.trading.requests import MarketOrderRequest, GetOrdersRequest
from alpaca.trading.enums import OrderSide, TimeInForce, OrderStatus
from sqlalchemy.orm import Session
from database.models import Strategy, Position, Trade, PerformanceMetric
from database.database import get_db
from datetime import datetime, timedelta
import logging
import os

logger = logging.getLogger(__name__)

class TradingService:
    def __init__(self):
        self.trading_client = TradingClient(
            api_key=os.getenv("ALPACA_API_KEY"),
            secret_key=os.getenv("ALPACA_SECRET_KEY"),
            paper=True  # Paper trading
        )
        self.stock_data_client = StockHistoricalDataClient(
            api_key=os.getenv("ALPACA_API_KEY"),
            secret_key=os.getenv("ALPACA_SECRET_KEY")
        )
        self.crypto_data_client = CryptoHistoricalDataClient(
            api_key=os.getenv("ALPACA_API_KEY"),
            secret_key=os.getenv("ALPACA_SECRET_KEY")
        )

    def place_order(self, strategy_id: int, symbol: str, side: OrderSide, quantity: float, db: Session):
        """Place an order and record it in database"""
        try:
            # Create Alpaca order
            order_request = MarketOrderRequest(
                symbol=symbol,
                qty=quantity,
                side=side,
                time_in_force=TimeInForce.DAY
            )
            
            alpaca_order = self.trading_client.submit_order(order_request)
            
            # Record trade in database
            trade = Trade(
                strategy_id=strategy_id,
                alpaca_order_id=alpaca_order.id,
                symbol=symbol,
                side=side.value,
                quantity=quantity,
                price=0.0,  # Will be updated when filled
                status=alpaca_order.status,
                created_at=datetime.utcnow()
            )
            
            db.add(trade)
            db.commit()
            
            logger.info(f"Order placed: {symbol} {side.value} {quantity} shares")
            return trade
            
        except Exception as e:
            logger.error(f"Error placing order: {e}")
            raise

    def update_positions(self, strategy_id: int, db: Session):
        """Sync positions from Alpaca to database"""
        try:
            alpaca_positions = self.trading_client.get_all_positions()
            
            for alpaca_pos in alpaca_positions:
                # Check if position exists in DB
                existing_pos = db.query(Position).filter(
                    Position.strategy_id == strategy_id,
                    Position.symbol == alpaca_pos.symbol
                ).first()
                
                if existing_pos:
                    # Update existing position
                    existing_pos.quantity = float(alpaca_pos.qty)
                    existing_pos.avg_price = float(alpaca_pos.avg_entry_price)
                    existing_pos.current_price = float(alpaca_pos.current_price)
                    existing_pos.market_value = float(alpaca_pos.market_value)
                    existing_pos.unrealized_pnl = float(alpaca_pos.unrealized_pl)
                    existing_pos.updated_at = datetime.utcnow()
                else:
                    # Create new position
                    new_pos = Position(
                        strategy_id=strategy_id,
                        symbol=alpaca_pos.symbol,
                        quantity=float(alpaca_pos.qty),
                        avg_price=float(alpaca_pos.avg_entry_price),
                        current_price=float(alpaca_pos.current_price),
                        market_value=float(alpaca_pos.market_value),
                        unrealized_pnl=float(alpaca_pos.unrealized_pl),
                        side="long" if float(alpaca_pos.qty) > 0 else "short"
                    )
                    db.add(new_pos)
            
            db.commit()
            
        except Exception as e:
            logger.error(f"Error updating positions: {e}")
            raise

    def update_filled_orders(self, strategy_id: int, db: Session):
        """Check for filled orders and update trades"""
        try:
            # Get pending trades from database
            pending_trades = db.query(Trade).filter(
                Trade.strategy_id == strategy_id,
                Trade.status == "pending"
            ).all()
            
            for trade in pending_trades:
                # Get order status from Alpaca
                alpaca_order = self.trading_client.get_order_by_id(trade.alpaca_order_id)
                
                if alpaca_order.status == OrderStatus.FILLED:
                    # Update trade with fill information
                    trade.status = "filled"
                    trade.price = float(alpaca_order.filled_avg_price)
                    trade.executed_at = alpaca_order.filled_at
                    
                    # Calculate commission (Alpaca is commission-free, but keeping for future)
                    trade.commission = 0.0
            
            db.commit()
            
        except Exception as e:
            logger.error(f"Error updating filled orders: {e}")
            raise

    def get_account_info(self):
        """Get account information from Alpaca"""
        try:
            account = self.trading_client.get_account()
            return {
                "buying_power": float(account.buying_power),
                "cash": float(account.cash),
                "portfolio_value": float(account.portfolio_value),
                "day_trade_count": int(account.daytrade_count),
                "equity": float(account.equity)
            }
        except Exception as e:
            logger.error(f"Error getting account info: {e}")
            raise

    def get_market_data(self, symbol: str, timeframe: str = "1Day", limit: int = 100):
        """Get historical market data"""
        try:
            # This is a simplified version - you'd implement proper timeframe handling
            if symbol.endswith("USD"):  # Crypto
                # Use crypto data client
                pass
            else:  # Stock
                # Use stock data client
                pass
            
            # Return mock data for now
            return {"symbol": symbol, "bars": []}
            
        except Exception as e:
            logger.error(f"Error getting market data: {e}")
            raise