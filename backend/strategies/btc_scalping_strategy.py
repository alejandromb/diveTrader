import asyncio
import json
import time
from datetime import datetime, timedelta
import pandas as pd
from sqlalchemy.orm import Session
from services.trading_service import TradingService
from services.performance_service import PerformanceService
from services.ai_analysis_service import AIAnalysisService
from alpaca.trading.enums import OrderSide
from alpaca.data.requests import CryptoBarsRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.data.historical import CryptoHistoricalDataClient
import logging
import os
from typing import Dict

logger = logging.getLogger(__name__)

class BTCScalpingStrategy:
    def __init__(self, strategy_id: int, trading_service: TradingService, 
                 performance_service: PerformanceService, db_session: Session, 
                 config: str = None):
        self.strategy_id = strategy_id
        self.trading_service = trading_service
        self.performance_service = performance_service
        self.db_session = db_session
        self.ai_analysis_service = AIAnalysisService()
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
            "max_positions": 1,
            # AI-enhanced settings
            "use_ai_analysis": True,
            "ai_confidence_threshold": 0.6,
            "combine_ai_with_technical": True,
            "ai_override_technical": False
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
        self.last_ai_analysis = None
        
        # Initialize crypto data client
        try:
            self.crypto_data_client = CryptoHistoricalDataClient(
                api_key=os.getenv("ALPACA_API_KEY"),
                secret_key=os.getenv("ALPACA_SECRET_KEY")
            )
            logger.info("Crypto data client initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing crypto data client: {e}")
            self.crypto_data_client = None
        
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
            if not self.crypto_data_client:
                logger.error("Crypto data client not initialized")
                return None
                
            # Get data for the last hour with 1-minute bars
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=2)  # Extended time window
            
            # Try different symbol formats that Alpaca might accept
            symbols_to_try = [self.symbol, "BTCUSD", "BTC-USD"]
            
            for symbol in symbols_to_try:
                try:
                    logger.info(f"Trying to get crypto bars for symbol: {symbol}")
                    request = CryptoBarsRequest(
                        symbol_or_symbols=[symbol],
                        timeframe=TimeFrame.Minute,
                        start=start_time,
                        end=end_time
                    )
                    
                    bars = self.crypto_data_client.get_crypto_bars(request)
                    
                    # Check if we got data (BarSet object)
                    if hasattr(bars, 'data') and symbol in bars.data and len(bars.data[symbol]) > 0:
                        logger.info(f"Successfully got {len(bars.data[symbol])} bars for {symbol}")
                        self.symbol = symbol  # Update to working symbol format
                        break
                    elif hasattr(bars, symbol) and bars[symbol] and len(bars[symbol]) > 0:
                        logger.info(f"Successfully got {len(bars[symbol])} bars for {symbol}")
                        self.symbol = symbol
                        break
                    else:
                        logger.warning(f"No data returned for symbol: {symbol}")
                        logger.warning(f"Bars object type: {type(bars)}, attributes: {dir(bars)}")
                        
                except Exception as e:
                    logger.warning(f"Failed to get data for symbol {symbol}: {e}")
                    continue
            else:
                logger.error("Failed to get data for any symbol format")
                return None
            
            # Convert to DataFrame - handle different BarSet structures
            bar_list = []
            data_source = None
            
            if hasattr(bars, 'data') and self.symbol in bars.data:
                data_source = bars.data[self.symbol]
            elif hasattr(bars, self.symbol):
                data_source = getattr(bars, self.symbol.replace('/', ''))  # Try without slash
            elif hasattr(bars, self.symbol.replace('/', '')):
                data_source = getattr(bars, self.symbol.replace('/', ''))
                
            if not data_source:
                logger.warning(f"No data found for {self.symbol} in bars object")
                return None
                
            for bar in data_source:
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
        """AI-enhanced market analysis and signal generation"""
        try:
            if len(bars_data) < self.config["long_ma_periods"]:
                return None
            
            # Convert DataFrame to list format for AI service
            price_data = []
            for _, row in bars_data.iterrows():
                price_data.append({
                    'timestamp': row['timestamp'],
                    'open': row['open'],
                    'high': row['high'],
                    'low': row['low'],
                    'close': row['close'],
                    'volume': row['volume']
                })
            
            # Calculate technical indicators
            technical_indicators = self.ai_analysis_service.calculate_technical_indicators(price_data)
            
            # Get traditional technical analysis signal
            traditional_signal = self._get_traditional_signal(bars_data, technical_indicators)
            
            # Get AI analysis if enabled
            if self.config.get("use_ai_analysis", True):
                try:
                    ai_analysis = self.ai_analysis_service.analyze_market_data(
                        symbol=self.symbol,
                        price_data=price_data,
                        technical_indicators=technical_indicators,
                        market_context={"strategy": "scalping", "timeframe": "1min"}
                    )
                    
                    ai_signal = ai_analysis.get("signal", "HOLD")
                    ai_confidence = ai_analysis.get("confidence", 0.5)
                    
                    logger.info(f"AI Analysis: {ai_signal} (confidence: {ai_confidence:.2f}) - {ai_analysis.get('reasoning', '')}")
                    
                    # Combine AI and traditional signals
                    final_signal = self._combine_signals(traditional_signal, ai_signal, ai_confidence)
                    
                    # Store AI analysis for monitoring
                    self.last_ai_analysis = ai_analysis
                    
                    return final_signal
                    
                except Exception as e:
                    logger.warning(f"AI analysis failed, using traditional analysis: {e}")
                    return traditional_signal
            else:
                return traditional_signal
                
        except Exception as e:
            logger.error(f"Error in market analysis: {e}")
            return None
    
    def _get_traditional_signal(self, bars_data: pd.DataFrame, technical_indicators: Dict) -> str:
        """Traditional technical analysis signal"""
        try:
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
            
            # Check for valid MA values
            if pd.isna(current_short_ma) or pd.isna(current_long_ma):
                return None
            
            # Buy signal: short MA crosses above long MA
            if (current_short_ma > current_long_ma and 
                latest['close'] > current_short_ma):
                return "BUY"
            
            return None
            
        except Exception as e:
            logger.error(f"Error in traditional analysis: {e}")
            return None
    
    def _combine_signals(self, traditional_signal: str, ai_signal: str, ai_confidence: float) -> str:
        """Combine traditional and AI signals intelligently"""
        try:
            # If AI confidence is low, rely on traditional
            if ai_confidence < self.config.get("ai_confidence_threshold", 0.6):
                logger.info(f"AI confidence too low ({ai_confidence:.2f}), using traditional signal: {traditional_signal}")
                return traditional_signal
            
            # If AI override is enabled and AI is confident
            if self.config.get("ai_override_technical", False) and ai_confidence > 0.8:
                logger.info(f"AI override enabled, using AI signal: {ai_signal}")
                return ai_signal
            
            # Combine signals - both must agree for BUY
            if self.config.get("combine_ai_with_technical", True):
                if traditional_signal == "BUY" and ai_signal == "BUY":
                    logger.info("Both AI and traditional analysis agree on BUY")
                    return "BUY"
                elif traditional_signal == "SELL" and ai_signal == "SELL":
                    logger.info("Both AI and traditional analysis agree on SELL")
                    return "SELL"
                else:
                    logger.info(f"Signals disagree - Traditional: {traditional_signal}, AI: {ai_signal} - HOLD")
                    return None
            else:
                # Use AI signal if available and confident
                if ai_confidence > 0.7:
                    return ai_signal
                else:
                    return traditional_signal
                    
        except Exception as e:
            logger.error(f"Error combining signals: {e}")
            return traditional_signal
            
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
        status = {
            "strategy_id": self.strategy_id,
            "is_running": self.is_running,
            "symbol": self.symbol,
            "has_position": self.current_position is not None,
            "config": self.config,
            "last_signal_time": self.last_signal_time.isoformat() if self.last_signal_time else None,
            "ai_enabled": self.config.get("use_ai_analysis", True),
            "ai_provider": getattr(self.ai_analysis_service, 'ai_provider', 'fallback')
        }
        
        # Add latest AI analysis if available
        if self.last_ai_analysis:
            status["last_ai_analysis"] = {
                "signal": self.last_ai_analysis.get("signal"),
                "confidence": self.last_ai_analysis.get("confidence"),
                "reasoning": self.last_ai_analysis.get("reasoning"),
                "risk_assessment": self.last_ai_analysis.get("risk_assessment"),
                "analysis_time": self.last_ai_analysis.get("analysis_time")
            }
        
        return status