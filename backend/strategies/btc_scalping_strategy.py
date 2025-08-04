import asyncio
import json
import time
from datetime import datetime, timedelta
import pandas as pd
from sqlalchemy.orm import Session
from services.trading_service import TradingService
from services.performance_service import PerformanceService
from alpaca.trading.enums import OrderSide
from alpaca.data.requests import CryptoBarsRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.data.historical import CryptoHistoricalDataClient
import logging
import os

logger = logging.getLogger(__name__)

class BTCScalpingStrategy:
    def __init__(self, strategy_id: int, trading_service: TradingService, 
                 performance_service: PerformanceService, db_session: Session, 
                 config: str = None):
        self.strategy_id = strategy_id
        self.trading_service = trading_service
        self.performance_service = performance_service
        self.db_session = db_session
        self.symbol = "BTC/USD"
        self.is_running = False
        
        # Default configuration
        self.config = {
            "position_size": 0.001,  # BTC amount per trade
            "take_profit_pct": 0.002,  # 0.2%
            "stop_loss_pct": 0.001,   # 0.1%
            "lookback_periods": 10,
            "short_ma_periods": 3,
            "long_ma_periods": 5,
            "min_volume": 1000,
            "max_positions": 1
        }
        
        # Load custom config if provided
        if config:
            try:
                custom_config = json.loads(config) if isinstance(config, str) else config
                self.config.update(custom_config)
            except Exception as e:
                logger.warning(f"Error loading config: {e}, using defaults")
                
        self.current_position = None
        self.last_signal_time = None
        
        # Initialize crypto data client
        self.crypto_data_client = CryptoHistoricalDataClient(
            api_key=os.getenv("ALPACA_API_KEY"),
            secret_key=os.getenv("ALPACA_SECRET_KEY")
        )
        
        logger.info(f"BTC Scalping Strategy initialized for strategy {strategy_id}")
        
    def start(self):
        """Start the strategy"""
        self.is_running = True
        logger.info(f"BTC Scalping Strategy {self.strategy_id} started")
        
    def stop(self):
        """Stop the strategy"""
        self.is_running = False
        logger.info(f"BTC Scalping Strategy {self.strategy_id} stopped")
        
        # Close any open positions
        if self.current_position:
            try:
                self._exit_position("strategy_stop")
            except Exception as e:
                logger.error(f"Error closing position on stop: {e}")
                
    def run_iteration(self):
        """Run one iteration of the strategy"""
        if not self.is_running:
            return
            
        try:
            # Get current market data
            bars_data = self._get_recent_bars()
            if bars_data is None or len(bars_data) < self.config["lookback_periods"]:
                logger.debug("Insufficient data for analysis")
                return
                
            # Analyze market and generate signals
            signal = self._analyze_market(bars_data)
            
            # Execute trading logic
            if signal:
                self._execute_signal(signal, bars_data.iloc[-1])
                
            # Check existing positions
            if self.current_position:
                self._manage_position(bars_data.iloc[-1])
                
        except Exception as e:
            logger.error(f"Error in strategy iteration: {e}")
            
    def _get_recent_bars(self) -> pd.DataFrame:
        """Get recent price bars for analysis"""
        try:
            # Get data for the last hour with 1-minute bars
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=1)
            
            request = CryptoBarsRequest(
                symbol_or_symbols=[self.symbol],
                timeframe=TimeFrame.Minute,
                start=start_time,
                end=end_time
            )
            
            bars = self.crypto_data_client.get_crypto_bars(request)
            
            if self.symbol not in bars:
                logger.warning(f"No data returned for {self.symbol}")
                return None
                
            # Convert to DataFrame
            bar_list = []
            for bar in bars[self.symbol]:
                bar_list.append({
                    'timestamp': bar.timestamp,
                    'open': float(bar.open),
                    'high': float(bar.high),
                    'low': float(bar.low),
                    'close': float(bar.close),
                    'volume': float(bar.volume)
                })
                
            df = pd.DataFrame(bar_list)
            if len(df) > 0:
                df = df.sort_values('timestamp').reset_index(drop=True)
                
            return df
            
        except Exception as e:
            logger.error(f"Error getting market data: {e}")
            return None
            
    def _analyze_market(self, bars_data: pd.DataFrame) -> str:
        """Analyze market data and generate trading signals"""
        try:
            if len(bars_data) < self.config["long_ma_periods"]:
                return None
                
            # Calculate moving averages
            bars_data['short_ma'] = bars_data['close'].rolling(
                window=self.config["short_ma_periods"]
            ).mean()
            bars_data['long_ma'] = bars_data['close'].rolling(
                window=self.config["long_ma_periods"]
            ).mean()
            
            # Get latest values
            latest = bars_data.iloc[-1]
            previous = bars_data.iloc[-2] if len(bars_data) > 1 else latest
            
            # Check volume
            if latest['volume'] < self.config["min_volume"]:
                return None
                
            # Avoid rapid-fire signals
            current_time = datetime.now()
            if (self.last_signal_time and 
                (current_time - self.last_signal_time).seconds < 300):  # 5 minutes
                return None
                
            # Moving average crossover strategy
            current_short_ma = latest['short_ma']
            current_long_ma = latest['long_ma']
            prev_short_ma = previous['short_ma']
            prev_long_ma = previous['long_ma']
            
            # Check for valid MA values
            if pd.isna(current_short_ma) or pd.isna(current_long_ma):
                return None
                
            # Buy signal: short MA crosses above long MA
            if (prev_short_ma <= prev_long_ma and 
                current_short_ma > current_long_ma and 
                latest['close'] > current_short_ma):
                return "BUY"
                
            # For now, we'll only implement buy signals
            # Sell signals would be implemented for short selling
            
            return None
            
        except Exception as e:
            logger.error(f"Error in market analysis: {e}")
            return None
            
    def _execute_signal(self, signal: str, current_bar):
        """Execute trading signal"""
        try:
            # Check if we already have a position
            if self.current_position is not None:
                logger.debug("Already have a position, skipping signal")
                return
                
            # Check max positions limit
            if self._count_open_positions() >= self.config["max_positions"]:
                logger.debug("Maximum positions reached, skipping signal")
                return
                
            if signal == "BUY":
                self._enter_position("buy", current_bar['close'])
                
        except Exception as e:
            logger.error(f"Error executing signal: {e}")
            
    def _enter_position(self, side: str, price: float):
        """Enter a new position"""
        try:
            # Place order through trading service
            order_side = OrderSide.BUY if side == "buy" else OrderSide.SELL
            trade = self.trading_service.place_order(
                strategy_id=self.strategy_id,
                symbol=self.symbol,
                side=order_side,
                quantity=self.config["position_size"],
                db=self.db_session
            )
            
            if trade:
                self.current_position = {
                    'trade_id': trade.id,
                    'side': side,
                    'entry_price': price,
                    'quantity': self.config["position_size"],
                    'timestamp': datetime.now(),
                    'take_profit_price': price * (1 + self.config["take_profit_pct"]) if side == "buy" else price * (1 - self.config["take_profit_pct"]),
                    'stop_loss_price': price * (1 - self.config["stop_loss_pct"]) if side == "buy" else price * (1 + self.config["stop_loss_pct"])
                }
                
                self.last_signal_time = datetime.now()
                logger.info(f"Entered {side} position: {self.config['position_size']} {self.symbol} at ${price:.2f}")
                
        except Exception as e:
            logger.error(f"Error entering position: {e}")
            
    def _manage_position(self, current_bar):
        """Manage existing position for exits"""
        if not self.current_position:
            return
            
        try:
            current_price = current_bar['close']
            entry_price = self.current_position['entry_price']
            side = self.current_position['side']
            
            should_exit = False
            exit_reason = ""
            
            if side == "buy":
                # Check take profit
                if current_price >= self.current_position['take_profit_price']:
                    should_exit = True
                    exit_reason = "take_profit"
                # Check stop loss
                elif current_price <= self.current_position['stop_loss_price']:
                    should_exit = True
                    exit_reason = "stop_loss"
                    
            if should_exit:
                self._exit_position(exit_reason, current_price)
                
        except Exception as e:
            logger.error(f"Error managing position: {e}")
            
    def _exit_position(self, reason: str, price: float = None):
        """Exit current position"""
        try:
            if not self.current_position:
                return
                
            # Place opposite order to close position
            side = self.current_position['side']
            opposite_side = OrderSide.SELL if side == "buy" else OrderSide.BUY
            
            trade = self.trading_service.place_order(
                strategy_id=self.strategy_id,
                symbol=self.symbol,
                side=opposite_side,
                quantity=self.current_position['quantity'],
                db=self.db_session
            )
            
            if trade:
                # Calculate P&L
                entry_price = self.current_position['entry_price']
                exit_price = price if price else entry_price  # Fallback if no price provided
                quantity = self.current_position['quantity']
                
                if side == "buy":
                    pnl = (exit_price - entry_price) * quantity
                else:
                    pnl = (entry_price - exit_price) * quantity
                    
                logger.info(f"Exited {side} position ({reason}): ${exit_price:.2f}, P&L: ${pnl:.2f}")
                
                # Clear position
                self.current_position = None
                
        except Exception as e:
            logger.error(f"Error exiting position: {e}")
            
    def _count_open_positions(self) -> int:
        """Count current open positions for this strategy"""
        try:
            from database.models import Position
            count = self.db_session.query(Position).filter(
                Position.strategy_id == self.strategy_id
            ).count()
            return count
        except Exception as e:
            logger.error(f"Error counting positions: {e}")
            return 0
            
    def get_status(self) -> dict:
        """Get strategy status"""
        return {
            "strategy_id": self.strategy_id,
            "is_running": self.is_running,
            "symbol": self.symbol,
            "has_position": self.current_position is not None,
            "config": self.config,
            "last_signal_time": self.last_signal_time.isoformat() if self.last_signal_time else None
        }