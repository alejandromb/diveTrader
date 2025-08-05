from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient, CryptoHistoricalDataClient
from alpaca.data.requests import StockLatestQuoteRequest, CryptoLatestQuoteRequest, StockBarsRequest, CryptoBarsRequest
from alpaca.data.timeframe import TimeFrame
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

    def get_current_price(self, symbol: str) -> float:
        """Get current market price for a symbol"""
        try:
            quotes = self.get_latest_quotes([symbol])
            if symbol in quotes:
                return quotes[symbol]['price']
            else:
                # Fallback prices
                fallback_prices = {
                    'BTC/USD': 75000.0,
                    'BTCUSD': 75000.0,
                    'AAPL': 185.0,
                    'TSLA': 260.0,
                    'SPY': 460.0,
                    'MSFT': 350.0
                }
                return fallback_prices.get(symbol, 100.0)
        except Exception as e:
            logger.error(f"Error getting current price for {symbol}: {e}")
            return 100.0  # Fallback price

    def place_order(self, strategy_id: int, symbol: str, side: OrderSide, quantity: float, db: Session, 
                   price: float = None, validate_risk: bool = True):
        """Place an order with optional risk validation"""
        try:
            # Get current market price if not provided
            if price is None:
                price = self.get_current_price(symbol)
            
            # Risk validation if enabled
            if validate_risk:
                from services.risk_management_service import RiskManagementService
                risk_service = RiskManagementService(self)
                
                is_valid, alerts = risk_service.validate_trade(
                    strategy_id, symbol, side, int(quantity), price, db
                )
                
                if not is_valid:
                    critical_alerts = [a for a in alerts if a.severity == "critical"]
                    if critical_alerts:
                        error_msg = f"Trade blocked by risk management: {critical_alerts[0].message}"
                        logger.warning(error_msg)
                        raise ValueError(error_msg)
                
                # Log any warnings
                for alert in alerts:
                    if alert.severity in ["high", "medium"]:
                        logger.warning(f"Risk warning: {alert.message}")
            
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
                price=price,
                status=alpaca_order.status,
                created_at=datetime.utcnow()
            )
            
            db.add(trade)
            db.commit()
            
            logger.info(f"Order placed: {symbol} {side.value} {quantity} shares at ${price}")
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

    def get_latest_quotes(self, symbols: list):
        """Get latest quotes for multiple symbols"""
        try:
            result = {}
            
            # Separate crypto and stock symbols
            crypto_symbols = []
            stock_symbols = []
            
            for symbol in symbols:
                if symbol in ['BTC/USD', 'ETH/USD', 'BTCUSD', 'ETHUSD']:
                    # Keep crypto symbols in BTC/USD format for Alpaca
                    if '/' not in symbol:
                        # Convert BTCUSD to BTC/USD
                        if symbol == 'BTCUSD':
                            normalized = 'BTC/USD'
                        elif symbol == 'ETHUSD':
                            normalized = 'ETH/USD'
                        else:
                            normalized = symbol
                    else:
                        normalized = symbol
                    crypto_symbols.append(normalized)
                else:
                    stock_symbols.append(symbol)
            
            # Get crypto quotes
            if crypto_symbols:
                try:
                    crypto_request = CryptoLatestQuoteRequest(symbol_or_symbols=crypto_symbols)
                    crypto_quotes = self.crypto_data_client.get_crypto_latest_quote(crypto_request)
                    
                    for symbol, quote in crypto_quotes.items():
                        display_symbol = symbol  # Should already be in BTC/USD format
                            
                        result[display_symbol] = {
                            'symbol': display_symbol,
                            'price': float(quote.bid_price),
                            'bid': float(quote.bid_price),
                            'ask': float(quote.ask_price),
                            'timestamp': quote.timestamp.isoformat()
                        }
                except Exception as e:
                    logger.error(f"Error getting crypto quotes: {e}")
                    # Add fallback data for crypto
                    for symbol in crypto_symbols:
                        display_symbol = 'BTC/USD' if 'BTC' in symbol else symbol
                        result[display_symbol] = {
                            'symbol': display_symbol,
                            'price': 75000.0 if 'BTC' in symbol else 2500.0,
                            'bid': 75000.0 if 'BTC' in symbol else 2500.0,
                            'ask': 75000.0 if 'BTC' in symbol else 2500.0,
                            'timestamp': datetime.utcnow().isoformat()
                        }
            
            # Get stock quotes
            if stock_symbols:
                try:
                    stock_request = StockLatestQuoteRequest(symbol_or_symbols=stock_symbols)
                    stock_quotes = self.stock_data_client.get_stock_latest_quote(stock_request)
                    
                    for symbol, quote in stock_quotes.items():
                        result[symbol] = {
                            'symbol': symbol,
                            'price': float(quote.bid_price) if quote.bid_price else float(quote.ask_price),
                            'bid': float(quote.bid_price) if quote.bid_price else 0,
                            'ask': float(quote.ask_price) if quote.ask_price else 0,
                            'timestamp': quote.timestamp.isoformat()
                        }
                except Exception as e:
                    logger.error(f"Error getting stock quotes: {e}")
                    # Add fallback data for stocks
                    stock_prices = {'AAPL': 185, 'TSLA': 260, 'SPY': 460, 'MSFT': 350}
                    for symbol in stock_symbols:
                        price = stock_prices.get(symbol, 100)
                        result[symbol] = {
                            'symbol': symbol,
                            'price': price,
                            'bid': price,
                            'ask': price,
                            'timestamp': datetime.utcnow().isoformat()
                        }
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting latest quotes: {e}")
            raise
    
    def get_market_data(self, symbol: str, timeframe: str = "1Day", limit: int = 100):
        """Get historical market data"""
        try:
            if symbol in ['BTC/USD', 'ETH/USD', 'BTCUSD', 'ETHUSD']:
                # Crypto historical data
                normalized_symbol = symbol.replace('/', '')
                request = CryptoBarsRequest(
                    symbol_or_symbols=[normalized_symbol],
                    timeframe=TimeFrame.Day,
                    limit=limit
                )
                bars = self.crypto_data_client.get_crypto_bars(request)
                
                bars_data = []
                for bar in bars[normalized_symbol]:
                    bars_data.append({
                        'timestamp': bar.timestamp.isoformat(),
                        'open': float(bar.open),
                        'high': float(bar.high),
                        'low': float(bar.low),
                        'close': float(bar.close),
                        'volume': float(bar.volume)
                    })
                
                return {"symbol": symbol, "bars": bars_data}
            else:
                # Stock historical data
                request = StockBarsRequest(
                    symbol_or_symbols=[symbol],
                    timeframe=TimeFrame.Day,
                    limit=limit
                )
                bars = self.stock_data_client.get_stock_bars(request)
                
                bars_data = []
                for bar in bars[symbol]:
                    bars_data.append({
                        'timestamp': bar.timestamp.isoformat(),
                        'open': float(bar.open),
                        'high': float(bar.high),
                        'low': float(bar.low),
                        'close': float(bar.close),
                        'volume': float(bar.volume)
                    })
                
                return {"symbol": symbol, "bars": bars_data}
            
        except Exception as e:
            logger.error(f"Error getting market data: {e}")
            raise

    def get_alpaca_positions(self):
        """Get all positions directly from Alpaca"""
        try:
            positions = self.trading_client.get_all_positions()
            return positions
        except Exception as e:
            logger.error(f"Error getting Alpaca positions: {e}")
            raise

    def place_manual_order(self, symbol: str, side: str, quantity: float = None, 
                          notional: float = None, order_type: str = "market", 
                          time_in_force: str = "day", limit_price: float = None):
        """Place a manual order directly through Alpaca (not tied to any strategy)"""
        try:
            # Convert side to OrderSide enum
            order_side = OrderSide.BUY if side.lower() == "buy" else OrderSide.SELL
            
            # Convert time_in_force to TimeInForce enum
            tif = TimeInForce.DAY if time_in_force.lower() == "day" else TimeInForce.GTC
            
            if order_type.lower() == "market":
                # Market order
                from alpaca.trading.requests import MarketOrderRequest
                if notional:
                    # Fractional shares using dollar amount
                    order_request = MarketOrderRequest(
                        symbol=symbol,
                        notional=notional,
                        side=order_side,
                        time_in_force=tif
                    )
                else:
                    # Regular shares order
                    order_request = MarketOrderRequest(
                        symbol=symbol,
                        qty=quantity,
                        side=order_side,
                        time_in_force=tif
                    )
            else:
                # Limit order
                from alpaca.trading.requests import LimitOrderRequest
                if limit_price is None:
                    raise ValueError("Limit price required for limit orders")
                
                if notional:
                    # Fractional shares limit order (if supported)
                    order_request = LimitOrderRequest(
                        symbol=symbol,
                        notional=notional,
                        side=order_side,
                        time_in_force=tif,
                        limit_price=limit_price
                    )
                else:
                    # Regular limit order
                    order_request = LimitOrderRequest(
                        symbol=symbol,
                        qty=quantity,
                        side=order_side,
                        time_in_force=tif,
                        limit_price=limit_price
                    )
            
            # Submit order to Alpaca
            order = self.trading_client.submit_order(order_request)
            
            order_description = f"${notional} of {symbol}" if notional else f"{quantity} shares of {symbol}"
            logger.info(f"Manual {side} order placed: {order_description}")
            return order
            
        except Exception as e:
            logger.error(f"Error placing manual order: {e}")
            raise