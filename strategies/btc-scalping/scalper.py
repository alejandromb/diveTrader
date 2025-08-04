import asyncio
from datetime import datetime, timedelta
import pandas as pd
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.data.live import CryptoDataStream
from alpaca.data.requests import CryptoBarsRequest
from alpaca.data.timeframe import TimeFrame
import logging

class BTCScalper:
    def __init__(self, trading_client: TradingClient, data_stream: CryptoDataStream):
        self.trading_client = trading_client
        self.data_stream = data_stream
        self.symbol = "BTC/USD"
        self.position_size = 0.001  # BTC amount per trade
        self.take_profit_pct = 0.002  # 0.2%
        self.stop_loss_pct = 0.001   # 0.1%
        self.is_running = False
        self.current_position = None
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    async def start_scalping(self):
        """Start the scalping strategy"""
        self.is_running = True
        self.logger.info("Starting BTC scalping strategy...")
        
        # Subscribe to real-time data
        self.data_stream.subscribe_bars(self.on_bar, self.symbol)
        
        try:
            await self.data_stream.run()
        except Exception as e:
            self.logger.error(f"Error in data stream: {e}")
        finally:
            self.is_running = False

    async def on_bar(self, bar):
        """Handle incoming price bars"""
        if not self.is_running:
            return
            
        self.logger.info(f"BTC Price: ${bar.close:.2f}")
        
        # Simple momentum strategy
        if self.current_position is None:
            await self._check_entry_signal(bar)
        else:
            await self._check_exit_signal(bar)

    async def _check_entry_signal(self, bar):
        """Check for entry signals"""
        # Get recent bars for analysis
        bars = await self._get_recent_bars()
        if len(bars) < 5:
            return
            
        # Simple moving average crossover
        short_ma = bars['close'].tail(3).mean()
        long_ma = bars['close'].tail(5).mean()
        
        if short_ma > long_ma and bar.close > short_ma:
            await self._enter_position("buy", bar.close)

    async def _check_exit_signal(self, bar):
        """Check for exit signals"""
        if not self.current_position:
            return
            
        entry_price = self.current_position['entry_price']
        current_price = bar.close
        
        if self.current_position['side'] == 'buy':
            profit_pct = (current_price - entry_price) / entry_price
            
            if profit_pct >= self.take_profit_pct:
                await self._exit_position("take_profit", current_price)
            elif profit_pct <= -self.stop_loss_pct:
                await self._exit_position("stop_loss", current_price)

    async def _enter_position(self, side, price):
        """Enter a new position"""
        try:
            order_request = MarketOrderRequest(
                symbol=self.symbol,
                qty=self.position_size,
                side=OrderSide.BUY if side == "buy" else OrderSide.SELL,
                time_in_force=TimeInForce.GTC
            )
            
            order = self.trading_client.submit_order(order_request)
            
            self.current_position = {
                'order_id': order.id,
                'side': side,
                'entry_price': price,
                'qty': self.position_size,
                'timestamp': datetime.now()
            }
            
            self.logger.info(f"Entered {side} position at ${price:.2f}")
            
        except Exception as e:
            self.logger.error(f"Error entering position: {e}")

    async def _exit_position(self, reason, price):
        """Exit current position"""
        try:
            if not self.current_position:
                return
                
            # Close position with opposite order
            side = OrderSide.SELL if self.current_position['side'] == 'buy' else OrderSide.BUY
            
            order_request = MarketOrderRequest(
                symbol=self.symbol,
                qty=self.current_position['qty'],
                side=side,
                time_in_force=TimeInForce.GTC
            )
            
            order = self.trading_client.submit_order(order_request)
            
            profit = (price - self.current_position['entry_price']) * self.current_position['qty']
            if self.current_position['side'] == 'sell':
                profit = -profit
                
            self.logger.info(f"Exited position ({reason}) at ${price:.2f}, P&L: ${profit:.2f}")
            
            self.current_position = None
            
        except Exception as e:
            self.logger.error(f"Error exiting position: {e}")

    async def _get_recent_bars(self, limit=10):
        """Get recent price bars for analysis"""
        try:
            request = CryptoBarsRequest(
                symbol_or_symbols=[self.symbol],
                timeframe=TimeFrame.Minute,
                start=datetime.now() - timedelta(minutes=limit),
                end=datetime.now()
            )
            
            bars = self.data_stream.get_crypto_bars(request)
            return pd.DataFrame([
                {
                    'timestamp': bar.timestamp,
                    'open': bar.open,
                    'high': bar.high,
                    'low': bar.low,
                    'close': bar.close,
                    'volume': bar.volume
                }
                for bar in bars[self.symbol]
            ])
            
        except Exception as e:
            self.logger.error(f"Error getting bars: {e}")
            return pd.DataFrame()

    def stop_scalping(self):
        """Stop the scalping strategy"""
        self.is_running = False
        self.logger.info("Stopping BTC scalping strategy...")
        
        # Close any open positions
        if self.current_position:
            asyncio.create_task(self._exit_position("strategy_stop", None))