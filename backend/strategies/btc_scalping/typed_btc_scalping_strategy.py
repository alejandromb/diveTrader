"""
Type-Safe BTC Scalping Strategy using SQLModel
Full type safety with automatic validation and IDE support
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
import pandas as pd
from sqlmodel import Session
from services.trading_service import TradingService
from services.performance_service import PerformanceService
from services.ai_analysis_service import AIAnalysisService
from strategies.typed_base_strategy import TypedBaseStrategy
from database.sqlmodel_models import BTCScalpingSettings, Position
from alpaca.trading.enums import OrderSide
from alpaca.data.requests import CryptoBarsRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.data.historical import CryptoHistoricalDataClient
import logging
import os
from typing import Dict, Optional, Any

logger = logging.getLogger(__name__)

class TypedBTCScalpingStrategy(TypedBaseStrategy):
    """Type-safe BTC Scalping Strategy with SQLModel validation"""

    def __init__(self, strategy_id: int, trading_service: TradingService, 
                 performance_service: PerformanceService, db_session: Session):
        super().__init__(strategy_id, db_session)
        self.trading_service = trading_service
        self.performance_service = performance_service
        self.ai_analysis_service = AIAnalysisService()
        self.symbol = "BTC/USD"
        self.is_running = False
        
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
        
        logger.info(f"Typed BTC Scalping Strategy initialized for strategy {strategy_id}")
    
    @property
    def btc_settings(self) -> Optional[BTCScalpingSettings]:
        """Get typed BTC scalping settings"""
        return self.settings if isinstance(self.settings, BTCScalpingSettings) else None
    
    def start(self) -> bool:
        """Start the strategy with validation"""
        try:
            is_valid, error = self.validate_settings()
            if not is_valid:
                logger.error(f"Strategy {self.strategy_id} has invalid settings: {error}")
                return False
            
            if not self.btc_settings:
                logger.error(f"No BTC settings found for strategy {self.strategy_id}")
                return False
                
            self.is_running = True
            logger.info(f"✅ Typed BTC Scalping Strategy {self.strategy_id} started")
            logger.info(f"Settings: position_size={self.btc_settings.position_size}, "
                       f"take_profit={self.btc_settings.take_profit_pct}, "
                       f"stop_loss={self.btc_settings.stop_loss_pct}")
            return True
        except Exception as e:
            logger.error(f"Error starting strategy {self.strategy_id}: {e}")
            return False

    def stop(self) -> bool:
        """Stop the strategy"""
        try:
            self.is_running = False
            logger.info(f"✅ Typed BTC Scalping Strategy {self.strategy_id} stopped")
            
            # Close any open positions
            if self.current_position:
                try:
                    self._exit_position("strategy_stop")
                except Exception as e:
                    logger.error(f"Error closing position on stop: {e}")
            return True
        except Exception as e:
            logger.error(f"Error stopping strategy {self.strategy_id}: {e}")
            return False

    def run_iteration(self):
        """Run one iteration of the strategy with typed settings"""
        if not self.is_running or not self.btc_settings:
            return
            
        try:
            # Get current market data
            bars_data = self._get_recent_bars()
            if bars_data is None or len(bars_data) < self.btc_settings.long_ma_periods:
                logger.info(f"[{datetime.now().strftime('%H:%M:%S')}] ASSESSMENT: Insufficient data for analysis "
                           f"(got {len(bars_data) if bars_data is not None else 0} bars, "
                           f"need {self.btc_settings.long_ma_periods})")
                return
                
            # Get current price for logging
            current_price = bars_data.iloc[-1]['close']
            current_volume = bars_data.iloc[-1]['volume']
            
            # Analyze market and generate signals
            signal = self._analyze_market(bars_data)
            
            # Log detailed assessment
            assessment_time = datetime.now().strftime('%H:%M:%S')
            if signal:
                logger.info(f"[{assessment_time}] SIGNAL: {signal} - Price: ${current_price:.2f}, Volume: {current_volume:.0f}")
                self._execute_signal(signal, bars_data.iloc[-1])
            else:
                logger.info(f"[{assessment_time}] NO ACTION - Price: ${current_price:.2f}, Volume: {current_volume:.0f} - Conditions not met")
                
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
                    logger.debug(f"Trying to get crypto bars for symbol: {symbol}")
                    request = CryptoBarsRequest(
                        symbol_or_symbols=[symbol],
                        timeframe=TimeFrame.Minute,
                        start=start_time,
                        end=end_time
                    )
                    
                    bars = self.crypto_data_client.get_crypto_bars(request)
                    
                    # Check if we got data (BarSet object)
                    if hasattr(bars, 'data') and symbol in bars.data and len(bars.data[symbol]) > 0:
                        logger.debug(f"Successfully got {len(bars.data[symbol])} bars for {symbol}")
                        self.symbol = symbol  # Update to working symbol format
                        break
                    elif hasattr(bars, symbol) and bars[symbol] and len(bars[symbol]) > 0:
                        logger.debug(f"Successfully got {len(bars[symbol])} bars for {symbol}")
                        self.symbol = symbol
                        break
                    else:
                        logger.warning(f"No data returned for symbol: {symbol}")
                        
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
        """AI-enhanced market analysis with typed settings"""
        try:
            if len(bars_data) < self.btc_settings.long_ma_periods:
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
            if self.btc_settings.use_ai_analysis:
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
        """Traditional technical analysis with typed settings"""
        try:
            # Calculate moving averages using typed settings
            bars_data['short_ma'] = bars_data['close'].rolling(
                window=self.btc_settings.short_ma_periods
            ).mean()
            bars_data['long_ma'] = bars_data['close'].rolling(
                window=self.btc_settings.long_ma_periods
            ).mean()
            
            # Get latest values
            latest = bars_data.iloc[-1]
            
            # Check volume with typed settings
            actual_volume = latest['volume']
            effective_volume = actual_volume
            
            # Handle paper trading zero volume
            if self.btc_settings.paper_trading_mode and actual_volume == 0:
                effective_volume = self.btc_settings.fallback_volume
                logger.info(f"  📄 Paper trading mode: Using fallback volume {effective_volume} (actual: {actual_volume})")
            
            if effective_volume < self.btc_settings.min_volume:
                if actual_volume == 0 and self.btc_settings.paper_trading_mode:
                    logger.info(f"  ✅ Volume check bypassed in paper trading mode")
                else:
                    logger.info(f"  ❌ Volume too low: {effective_volume:.0f} < {self.btc_settings.min_volume}")
                    return None
            
            # Avoid rapid-fire signals
            current_time = datetime.now()
            if (self.last_signal_time and 
                (current_time - self.last_signal_time).seconds < 300):  # 5 minutes
                time_since_last = (current_time - self.last_signal_time).seconds
                logger.info(f"  ❌ Cooldown active: {time_since_last}s since last signal (need 300s)")
                return None
            
            # Moving average crossover strategy
            current_short_ma = latest['short_ma']
            current_long_ma = latest['long_ma']
            current_price = latest['close']
            
            # Check for valid MA values
            if pd.isna(current_short_ma) or pd.isna(current_long_ma):
                logger.info(f"  ❌ Invalid MA values: Short MA={current_short_ma}, Long MA={current_long_ma}")
                return None
            
            # Log current conditions
            short_above_long = current_short_ma > current_long_ma
            price_above_short = current_price > current_short_ma
            
            logger.info(f"  📊 Technical Analysis:")
            logger.info(f"     Short MA ({self.btc_settings.short_ma_periods}): ${current_short_ma:.2f}")
            logger.info(f"     Long MA ({self.btc_settings.long_ma_periods}): ${current_long_ma:.2f}")
            logger.info(f"     Price > Short MA: {price_above_short} (${current_price:.2f} > ${current_short_ma:.2f})")
            logger.info(f"     Short MA > Long MA: {short_above_long}")
            
            # Buy signal: short MA crosses above long MA
            if short_above_long and price_above_short:
                logger.info(f"  ✅ BUY conditions met!")
                return "BUY"
            else:
                logger.info(f"  ❌ BUY conditions not met")
            
            return None
            
        except Exception as e:
            logger.error(f"Error in traditional analysis: {e}")
            return None
    
    def _combine_signals(self, traditional_signal: str, ai_signal: str, ai_confidence: float) -> str:
        """Combine traditional and AI signals with typed settings"""
        try:
            # If AI confidence is low, rely on traditional
            if ai_confidence < self.btc_settings.ai_confidence_threshold:
                logger.info(f"AI confidence too low ({ai_confidence:.2f}), using traditional signal: {traditional_signal}")
                return traditional_signal
            
            # Combine signals - both must agree for BUY
            if self.btc_settings.combine_ai_with_technical:
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
        """Execute trading signal with typed settings"""
        try:
            # Check if we already have a position
            if self.current_position is not None:
                logger.debug("Already have a position, skipping signal")
                return
                
            # Check max positions limit using typed settings
            if self._count_open_positions() >= self.btc_settings.max_positions:
                logger.debug("Maximum positions reached, skipping signal")
                return
                
            if signal == "BUY":
                self._enter_position("buy", current_bar['close'])
                
        except Exception as e:
            logger.error(f"Error executing signal: {e}")
    
    def _enter_position(self, side: str, price: float):
        """Enter a new position using typed settings"""
        try:
            # Place order through trading service using typed settings
            order_side = OrderSide.BUY if side == "buy" else OrderSide.SELL
            trade = self.trading_service.place_order(
                strategy_id=self.strategy_id,
                symbol=self.symbol,
                side=order_side,
                quantity=self.btc_settings.position_size,  # Type-safe access
                db=self.db_session
            )
            
            if trade:
                self.current_position = {
                    'trade_id': trade.id,
                    'side': side,
                    'entry_price': price,
                    'quantity': self.btc_settings.position_size,
                    'timestamp': datetime.now(),
                    'take_profit_price': price * (1 + self.btc_settings.take_profit_pct) if side == "buy" else price * (1 - self.btc_settings.take_profit_pct),
                    'stop_loss_price': price * (1 - self.btc_settings.stop_loss_pct) if side == "buy" else price * (1 + self.btc_settings.stop_loss_pct)
                }
                
                self.last_signal_time = datetime.now()
                logger.info(f"Entered {side} position: {self.btc_settings.position_size} {self.symbol} at ${price:.2f}")
                
        except Exception as e:
            logger.error(f"Error entering position: {e}")
    
    def _manage_position(self, current_bar):
        """Manage existing position for exits"""
        if not self.current_position:
            return
            
        try:
            current_price = current_bar['close']
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
            from sqlmodel import select
            statement = select(Position).where(Position.strategy_id == self.strategy_id)
            positions = self.db_session.exec(statement).all()
            return len(positions)
        except Exception as e:
            logger.error(f"Error counting positions: {e}")
            return 0
    
    def get_status(self) -> dict:
        """Get strategy status with typed settings"""
        if not self.strategy or not self.btc_settings:
            return {"error": "Strategy or settings not loaded"}
        
        status = {
            "strategy_id": self.strategy_id,
            "is_running": self.is_running,
            "symbol": self.symbol,
            "has_position": self.current_position is not None,
            "settings": self.get_settings_dict(),
            "last_signal_time": self.last_signal_time.isoformat() if self.last_signal_time else None,
            "ai_enabled": self.btc_settings.use_ai_analysis,
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
    
    def backtest(self, data: pd.DataFrame, config: Dict[str, Any], 
                initial_capital: float, days_back: int) -> 'BacktestResult':
        """
        Run backtesting for BTC scalping strategy
        
        This method contains the actual BTC scalping logic extracted from the 
        enhanced backtesting service, but now properly encapsulated in the strategy.
        """
        from strategies.base_strategy import BacktestResult, BacktestTrade
        from datetime import datetime, timedelta
        
        logger.info(f"Starting BTC scalping backtest: {len(data)} data points, ${initial_capital} initial capital")
        
        try:
            # Merge strategy settings with config
            default_config = {
                "short_ma_periods": 5,
                "long_ma_periods": 20,
                "rsi_oversold": 30,
                "rsi_overbought": 70,
                "min_volume": 1000,
                "position_size_pct": 0.1  # 10% of capital per trade
            }
            
            btc_config = config.get('btc_scalping', {})
            final_config = {**default_config, **btc_config}
            
            # Add technical indicators to data
            data = data.copy()
            data['short_ma'] = data['close'].rolling(window=final_config["short_ma_periods"]).mean()
            data['long_ma'] = data['close'].rolling(window=final_config["long_ma_periods"]).mean()
            data['rsi'] = self._calculate_rsi(data['close'], 14)
            
            # Trading simulation variables
            trades = []
            capital = initial_capital
            current_position = None
            equity_curve = []
            max_portfolio_value = initial_capital
            
            # Run simulation
            for i in range(final_config["long_ma_periods"], len(data)):
                current_bar = data.iloc[i]
                timestamp = current_bar['timestamp']
                price = current_bar['close']
                
                # Record portfolio value
                portfolio_value = capital
                if current_position:
                    position_value = current_position['quantity'] * price
                    portfolio_value = capital + position_value
                
                equity_curve.append({
                    'timestamp': timestamp,
                    'portfolio_value': portfolio_value,
                    'cash': capital
                })
                
                max_portfolio_value = max(max_portfolio_value, portfolio_value)
                
                # Check for exit signals first
                if current_position:
                    should_exit, exit_reason = self._check_exit_condition(current_position, current_bar, final_config)
                    
                    if should_exit:
                        # Execute exit trade
                        pnl = self._calculate_position_pnl(current_position, price)
                        capital += pnl
                        
                        trade = BacktestTrade(
                            timestamp=timestamp,
                            symbol="BTC/USD",
                            side="sell" if current_position['side'] == "buy" else "buy",
                            quantity=current_position['quantity'],
                            price=price,
                            pnl=pnl,
                            reason=exit_reason
                        )
                        trades.append(trade)
                        current_position = None
                
                # Check for entry signals
                if not current_position:
                    entry_signal = self._check_entry_signal(data.iloc[max(0, i-10):i+1], final_config)
                    
                    if entry_signal in ['buy', 'sell']:
                        # Calculate position size
                        position_value = capital * final_config["position_size_pct"]
                        quantity = position_value / price
                        
                        current_position = {
                            'side': entry_signal,
                            'entry_price': price,
                            'entry_time': timestamp,
                            'quantity': quantity
                        }
                        
                        # Record entry trade
                        trade = BacktestTrade(
                            timestamp=timestamp,
                            symbol="BTC/USD", 
                            side=entry_signal,
                            quantity=quantity,
                            price=price,
                            reason="Entry signal"
                        )
                        trades.append(trade)
            
            # Calculate final metrics
            final_capital = capital
            if current_position:
                # Close any remaining position
                final_price = data.iloc[-1]['close']
                pnl = self._calculate_position_pnl(current_position, final_price)
                final_capital += pnl
                
                # Add final exit trade
                trades.append(BacktestTrade(
                    timestamp=data.iloc[-1]['timestamp'],
                    symbol="BTC/USD",
                    side="sell" if current_position['side'] == "buy" else "buy",
                    quantity=current_position['quantity'], 
                    price=final_price,
                    pnl=pnl,
                    reason="Backtest end"
                ))
            
            # Calculate performance metrics
            total_return = final_capital - initial_capital
            total_return_pct = (total_return / initial_capital) * 100
            
            winning_trades = len([t for t in trades if t.pnl and t.pnl > 0])
            losing_trades = len([t for t in trades if t.pnl and t.pnl < 0])
            win_rate = (winning_trades / len(trades)) * 100 if trades else 0
            
            # Calculate max drawdown
            peak = initial_capital
            max_drawdown = 0
            for point in equity_curve:
                if point['portfolio_value'] > peak:
                    peak = point['portfolio_value']
                drawdown = (peak - point['portfolio_value']) / peak * 100
                max_drawdown = max(max_drawdown, drawdown)
            
            # Calculate Sharpe ratio (simplified)
            returns = []
            for i in range(1, len(equity_curve)):
                prev_val = equity_curve[i-1]['portfolio_value']
                curr_val = equity_curve[i]['portfolio_value']
                daily_return = (curr_val - prev_val) / prev_val
                returns.append(daily_return)
            
            if returns:
                import numpy as np
                sharpe_ratio = np.mean(returns) / np.std(returns) * np.sqrt(252) if np.std(returns) > 0 else 0
            else:
                sharpe_ratio = 0
            
            # Create result
            result = BacktestResult(
                strategy_type="btc_scalping",
                symbol="BTC/USD",
                period=f"{days_back} days",
                start_date=data.iloc[0]['timestamp'] if len(data) > 0 else datetime.now(),
                end_date=data.iloc[-1]['timestamp'] if len(data) > 0 else datetime.now(),
                initial_capital=initial_capital,
                final_capital=final_capital,
                total_return=total_return,
                total_return_pct=total_return_pct,
                total_trades=len(trades),
                winning_trades=winning_trades,
                losing_trades=losing_trades,
                win_rate=win_rate,
                max_drawdown=max_drawdown,
                sharpe_ratio=sharpe_ratio,
                trades=trades,
                equity_curve=equity_curve,
                metadata={"config": final_config, "data_points": len(data)}
            )
            
            logger.info(f"BTC backtest completed: ${final_capital:.2f} final, {len(trades)} trades, {win_rate:.1f}% win rate")
            return result
            
        except Exception as e:
            logger.error(f"Error in BTC backtest: {e}")
            raise
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI indicator"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _check_exit_condition(self, position: dict, current_bar: pd.Series, config: dict) -> tuple[bool, str]:
        """Check if position should be exited"""
        # Simple exit conditions - can be enhanced
        entry_price = position['entry_price']
        current_price = current_bar['close']
        
        # Stop loss: 2% loss
        if position['side'] == 'buy' and current_price < entry_price * 0.98:
            return True, "Stop loss"
        elif position['side'] == 'sell' and current_price > entry_price * 1.02:
            return True, "Stop loss"
        
        # Take profit: 1% gain
        if position['side'] == 'buy' and current_price > entry_price * 1.01:
            return True, "Take profit"
        elif position['side'] == 'sell' and current_price < entry_price * 0.99:
            return True, "Take profit"
        
        return False, ""
    
    def _check_entry_signal(self, recent_data: pd.DataFrame, config: dict) -> str:
        """Check for entry signals based on technical indicators"""
        if len(recent_data) < 2:
            return "hold"
        
        current = recent_data.iloc[-1]
        previous = recent_data.iloc[-2]
        
        # Simple MA crossover strategy
        if (current['short_ma'] > current['long_ma'] and 
            previous['short_ma'] <= previous['long_ma'] and
            current['rsi'] < config['rsi_overbought']):
            return "buy"
        elif (current['short_ma'] < current['long_ma'] and 
              previous['short_ma'] >= previous['long_ma'] and
              current['rsi'] > config['rsi_oversold']):
            return "sell"
        
        return "hold"
    
    def _calculate_position_pnl(self, position: dict, current_price: float) -> float:
        """Calculate P&L for a position"""
        entry_price = position['entry_price']
        quantity = position['quantity']
        
        if position['side'] == 'buy':
            return (current_price - entry_price) * quantity
        else:
            return (entry_price - current_price) * quantity