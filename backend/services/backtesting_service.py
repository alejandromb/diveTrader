from datetime import datetime, timedelta
import pandas as pd
from alpaca.data.historical import CryptoHistoricalDataClient
from alpaca.data.requests import CryptoBarsRequest
from alpaca.data.timeframe import TimeFrame
import logging
import os
from typing import Dict, List

logger = logging.getLogger(__name__)

class BacktestingService:
    def __init__(self):
        self.crypto_data_client = CryptoHistoricalDataClient(
            api_key=os.getenv("ALPACA_API_KEY"),
            secret_key=os.getenv("ALPACA_SECRET_KEY")
        )
        
    def run_backtest(self, strategy_config: Dict, symbol: str = "BTC/USD", 
                    days_back: int = 30, initial_capital: float = 10000.0) -> Dict:
        """Run a backtest for the BTC scalping strategy"""
        try:
            # Get historical data
            end_time = datetime.now()
            start_time = end_time - timedelta(days=days_back)
            
            bars_data = self._get_historical_data(symbol, start_time, end_time)
            if bars_data is None or len(bars_data) < 20:
                raise ValueError("Insufficient historical data for backtesting")
                
            # Run strategy simulation
            results = self._simulate_strategy(bars_data, strategy_config, initial_capital)
            
            # Calculate performance metrics
            performance = self._calculate_performance_metrics(results, initial_capital)
            
            return {
                "symbol": symbol,
                "period": f"{days_back} days",
                "start_date": start_time.strftime("%Y-%m-%d"),
                "end_date": end_time.strftime("%Y-%m-%d"),
                "initial_capital": initial_capital,
                "final_capital": performance["final_capital"],
                "total_return": performance["total_return"],
                "total_return_pct": performance["total_return_pct"],
                "total_trades": performance["total_trades"],
                "winning_trades": performance["winning_trades"],
                "losing_trades": performance["losing_trades"],
                "win_rate": performance["win_rate"],
                "avg_win": performance["avg_win"],
                "avg_loss": performance["avg_loss"],
                "max_drawdown": performance["max_drawdown"],
                "sharpe_ratio": performance["sharpe_ratio"],
                "trades": results["trades"][-50:]  # Last 50 trades for review
            }
            
        except Exception as e:
            logger.error(f"Error running backtest: {e}")
            raise
            
    def _get_historical_data(self, symbol: str, start_time: datetime, 
                           end_time: datetime) -> pd.DataFrame:
        """Get historical price data"""
        try:
            request = CryptoBarsRequest(
                symbol_or_symbols=[symbol],
                timeframe=TimeFrame.Minute,
                start=start_time,
                end=end_time
            )
            
            bars = self.crypto_data_client.get_crypto_bars(request)
            
            if symbol not in bars:
                return None
                
            # Convert to DataFrame
            bar_list = []
            for bar in bars[symbol]:
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
            logger.error(f"Error getting historical data: {e}")
            return None
            
    def _simulate_strategy(self, bars_data: pd.DataFrame, config: Dict, 
                          initial_capital: float) -> Dict:
        """Simulate the trading strategy on historical data"""
        
        # Default configuration
        default_config = {
            "position_size": 0.001,
            "take_profit_pct": 0.002,
            "stop_loss_pct": 0.001,
            "short_ma_periods": 3,
            "long_ma_periods": 5,
            "min_volume": 1000
        }
        default_config.update(config)
        
        # Calculate moving averages
        bars_data['short_ma'] = bars_data['close'].rolling(
            window=default_config["short_ma_periods"]
        ).mean()
        bars_data['long_ma'] = bars_data['close'].rolling(
            window=default_config["long_ma_periods"]
        ).mean()
        
        trades = []
        capital = initial_capital
        current_position = None
        equity_curve = []
        
        for i in range(default_config["long_ma_periods"], len(bars_data)):
            current_bar = bars_data.iloc[i]
            prev_bar = bars_data.iloc[i-1]
            
            timestamp = current_bar['timestamp']
            price = current_bar['close']
            
            # Check for exit signals first
            if current_position:
                should_exit, exit_reason = self._check_exit_condition(
                    current_position, current_bar, default_config
                )
                
                if should_exit:
                    # Close position
                    pnl = self._calculate_pnl(current_position, price)
                    capital += pnl
                    
                    trade = {
                        "entry_time": current_position["entry_time"],
                        "exit_time": timestamp,
                        "side": current_position["side"],
                        "entry_price": current_position["entry_price"],
                        "exit_price": price,
                        "quantity": current_position["quantity"],
                        "pnl": pnl,
                        "pnl_pct": (pnl / (current_position["entry_price"] * current_position["quantity"])) * 100,
                        "exit_reason": exit_reason
                    }
                    trades.append(trade)
                    current_position = None
                    
            # Check for entry signals
            if not current_position:
                signal = self._check_entry_signal(prev_bar, current_bar, default_config)
                
                if signal == "BUY":
                    # Enter position
                    position_value = price * default_config["position_size"]
                    if capital >= position_value:  # Check if we have enough capital
                        current_position = {
                            "side": "buy",
                            "entry_time": timestamp,
                            "entry_price": price,
                            "quantity": default_config["position_size"]
                        }
                        capital -= position_value  # Reserve capital for position
                        
            # Record equity curve
            portfolio_value = capital
            if current_position:
                portfolio_value += current_position["quantity"] * price
                
            equity_curve.append({
                "timestamp": timestamp,
                "capital": capital,
                "portfolio_value": portfolio_value
            })
            
        # Close any remaining position at the end
        if current_position:
            final_price = bars_data.iloc[-1]['close']
            pnl = self._calculate_pnl(current_position, final_price)
            capital += pnl
            
            trade = {
                "entry_time": current_position["entry_time"],
                "exit_time": bars_data.iloc[-1]['timestamp'],
                "side": current_position["side"],
                "entry_price": current_position["entry_price"],
                "exit_price": final_price,
                "quantity": current_position["quantity"],
                "pnl": pnl,
                "pnl_pct": (pnl / (current_position["entry_price"] * current_position["quantity"])) * 100,
                "exit_reason": "backtest_end"
            }
            trades.append(trade)
            
        return {
            "trades": trades,
            "final_capital": capital,
            "equity_curve": equity_curve
        }
        
    def _check_entry_signal(self, prev_bar, current_bar, config) -> str:
        """Check for entry signals"""
        if (pd.isna(current_bar['short_ma']) or pd.isna(current_bar['long_ma']) or
            pd.isna(prev_bar['short_ma']) or pd.isna(prev_bar['long_ma'])):
            return None
            
        # Volume check
        if current_bar['volume'] < config["min_volume"]:
            return None
            
        # Moving average crossover
        if (prev_bar['short_ma'] <= prev_bar['long_ma'] and 
            current_bar['short_ma'] > current_bar['long_ma'] and 
            current_bar['close'] > current_bar['short_ma']):
            return "BUY"
            
        return None
        
    def _check_exit_condition(self, position, current_bar, config):
        """Check if position should be exited"""
        entry_price = position["entry_price"]
        current_price = current_bar['close']
        
        if position["side"] == "buy":
            profit_pct = (current_price - entry_price) / entry_price
            
            if profit_pct >= config["take_profit_pct"]:
                return True, "take_profit"
            elif profit_pct <= -config["stop_loss_pct"]:
                return True, "stop_loss"
                
        return False, None
        
    def _calculate_pnl(self, position, exit_price):
        """Calculate P&L for a position"""
        entry_price = position["entry_price"]
        quantity = position["quantity"]
        
        if position["side"] == "buy":
            return (exit_price - entry_price) * quantity
        else:
            return (entry_price - exit_price) * quantity
            
    def _calculate_performance_metrics(self, results, initial_capital):
        """Calculate comprehensive performance metrics"""
        trades = results["trades"]
        final_capital = results["final_capital"]
        equity_curve = results["equity_curve"]
        
        if not trades:
            return {
                "final_capital": final_capital,
                "total_return": 0,
                "total_return_pct": 0,
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "win_rate": 0,
                "avg_win": 0,
                "avg_loss": 0,
                "max_drawdown": 0,
                "sharpe_ratio": 0
            }
            
        # Basic metrics
        total_return = final_capital - initial_capital
        total_return_pct = (total_return / initial_capital) * 100
        
        winning_trades = [t for t in trades if t["pnl"] > 0]
        losing_trades = [t for t in trades if t["pnl"] < 0]
        
        win_rate = (len(winning_trades) / len(trades)) * 100 if trades else 0
        avg_win = sum(t["pnl"] for t in winning_trades) / len(winning_trades) if winning_trades else 0
        avg_loss = sum(t["pnl"] for t in losing_trades) / len(losing_trades) if losing_trades else 0
        
        # Calculate max drawdown
        max_drawdown = 0
        peak = initial_capital
        
        for point in equity_curve:
            portfolio_value = point["portfolio_value"]
            if portfolio_value > peak:
                peak = portfolio_value
            drawdown = (peak - portfolio_value) / peak * 100
            max_drawdown = max(max_drawdown, drawdown)
            
        # Simple Sharpe ratio calculation
        daily_returns = []
        for i in range(1, len(equity_curve)):
            prev_value = equity_curve[i-1]["portfolio_value"]
            curr_value = equity_curve[i]["portfolio_value"]
            daily_return = (curr_value - prev_value) / prev_value
            daily_returns.append(daily_return)
            
        if daily_returns:
            avg_return = sum(daily_returns) / len(daily_returns)
            return_std = pd.Series(daily_returns).std()
            sharpe_ratio = (avg_return / return_std) * (252 ** 0.5) if return_std > 0 else 0
        else:
            sharpe_ratio = 0
            
        return {
            "final_capital": final_capital,
            "total_return": total_return,
            "total_return_pct": total_return_pct,
            "total_trades": len(trades),
            "winning_trades": len(winning_trades),
            "losing_trades": len(losing_trades),
            "win_rate": win_rate,
            "avg_win": avg_win,
            "avg_loss": avg_loss,
            "max_drawdown": max_drawdown,
            "sharpe_ratio": sharpe_ratio
        }