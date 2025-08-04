# DiveTrader Backtesting System 📊

**Comprehensive Historical Performance Testing for Trading Strategies**

## Overview

DiveTrader's backtesting system allows you to test your trading strategies against historical market data to evaluate their performance before risking real capital. The system supports both BTC scalping and portfolio distributor strategies with detailed performance analytics.

## Current Implementation Status

### ✅ **What's Working**
- **BTC Scalping Backtest**: Full implementation with AI-enhanced signals
- **Historical Data Integration**: Alpaca API with fallback to synthetic data  
- **Comprehensive Metrics**: 15+ performance indicators
- **Frontend UI**: Modal interface accessible from strategy cards
- **API Endpoints**: RESTful API for backtest execution

### ⚠️ **Current Limitations**
- **Data Availability**: Limited historical crypto data from Alpaca
- **Portfolio Backtest**: Partially implemented (needs completion)
- **Real vs Synthetic**: May use synthetic data when real data unavailable
- **Timeframe**: Limited to available historical data range

## Backtesting Features

### 🎯 **Strategy Coverage**

#### **BTC Scalping Strategy**
- **Technical Analysis**: Moving average crossovers, RSI, Bollinger Bands
- **AI Integration**: Confidence-based signal filtering
- **Risk Management**: Take profit, stop loss, trailing stops
- **Position Sizing**: Configurable position sizes and limits
- **Enhanced Signals**: Multi-indicator confirmation system

#### **Portfolio Distributor Strategy** 
- **Dollar-Cost Averaging**: Scheduled investment simulation
- **Multi-Asset**: Test across different stock combinations
- **Rebalancing**: Portfolio rebalancing simulation
- **Allocation Testing**: Different percentage allocations

### 📈 **Performance Metrics**

#### **Basic Metrics**
- **Total Return**: Absolute and percentage gains/losses
- **Win Rate**: Percentage of profitable trades
- **Trade Statistics**: Total, winning, and losing trades
- **Average Win/Loss**: Mean profit and loss per trade

#### **Advanced Metrics**  
- **Sharpe Ratio**: Risk-adjusted returns
- **Maximum Drawdown**: Largest peak-to-trough decline
- **Profit Factor**: Gross profit / Gross loss ratio
- **Recovery Factor**: Return / Maximum drawdown
- **Value at Risk (VaR)**: 5th percentile risk measure

#### **Risk Analysis**
- **Volatility**: Standard deviation of returns
- **Consecutive Losses**: Maximum losing streak
- **Time Underwater**: Days spent in drawdown
- **Downside Deviation**: Volatility of negative returns

#### **Comparison Analysis**
- **Buy & Hold**: Strategy vs buy-and-hold comparison
- **Excess Return**: Strategy outperformance
- **Monthly Breakdown**: Month-by-month performance

## How to Use Backtesting

### **From the UI**
1. **Navigate** to your strategy card in the dashboard
2. **Click** the "📊 Backtest" button  
3. **Configure** test parameters:
   - **Days Back**: 7-365 days of historical data
   - **Initial Capital**: Starting capital amount
   - **Strategy Config**: Custom parameters (optional)
4. **Run Test** and analyze results

### **API Usage**
```bash
curl -X POST http://localhost:8000/api/strategies/1/backtest \
  -H "Content-Type: application/json" \
  -d '{
    "days_back": 30,
    "initial_capital": 10000,
    "config": {
      "btc_scalping": {
        "position_size": 0.001,
        "take_profit_pct": 0.002,
        "stop_loss_pct": 0.001
      }
    }
  }'
```

## Backtest Configuration

### **BTC Scalping Parameters**
```json
{
  "btc_scalping": {
    "position_size": 0.001,           // BTC per trade
    "take_profit_pct": 0.002,         // 0.2% take profit
    "stop_loss_pct": 0.001,           // 0.1% stop loss  
    "short_ma_periods": 3,            // Fast MA periods
    "long_ma_periods": 5,             // Slow MA periods
    "min_volume": 1000,               // Minimum volume filter
    "trailing_stop_pct": 0.0005,      // Trailing stop %
    "rsi_overbought": 70,             // RSI upper limit
    "rsi_oversold": 30                // RSI lower limit
  }
}
```

### **Portfolio Distributor Parameters**
```json
{
  "portfolio_distributor": {
    "symbols": ["AAPL", "MSFT", "GOOGL", "TSLA", "SPY"],
    "allocation_weights": {
      "AAPL": 25.0,
      "MSFT": 25.0, 
      "GOOGL": 20.0,
      "TSLA": 15.0,
      "SPY": 15.0
    },
    "investment_frequency": "weekly",  // weekly/monthly
    "investment_amount": 1000,         // Amount per investment
    "rebalance_threshold": 5.0         // % drift before rebalance
  }
}
```

## Data Sources & Fallbacks

### **Primary Data Source**
- **Alpaca Markets API**: Real historical market data
- **Crypto Data**: BTC/USD hourly bars  
- **Stock Data**: Daily bars for portfolio symbols
- **Data Range**: Up to 1 year of historical data

### **Fallback System**
When real data is unavailable, the system uses:

#### **Synthetic BTC Data**
- **Geometric Brownian Motion**: Realistic price movements
- **Volatility Modeling**: 4% daily volatility (typical for BTC)
- **Volume Simulation**: Correlated with price movements
- **OHLC Generation**: Proper high/low/open/close relationships

#### **Synthetic Stock Data**
- **Individual Characteristics**: Different volatility per symbol
- **Realistic Pricing**: Based on actual recent price levels
- **Volume Modeling**: Appropriate volume ranges per symbol
- **Correlation**: Inter-stock price relationships

## Interpreting Results

### **Understanding the Output**

#### **Performance Summary**
```json
{
  "total_return_pct": 5.2,           // 5.2% total return
  "win_rate": 68.5,                  // 68.5% of trades profitable
  "sharpe_ratio": 1.45,              // Good risk-adjusted returns
  "max_drawdown": 3.2,               // 3.2% maximum decline
  "profit_factor": 2.1               // $2.10 profit per $1 loss
}
```

#### **Trade Analysis**
- **Total Trades**: Higher is better for statistical significance
- **Win Rate**: 60%+ is excellent, 50%+ is good  
- **Average Win vs Loss**: Win should be > Loss for profitability
- **Trade Duration**: Shorter for scalping, longer for swing trading

#### **Risk Metrics**
- **Sharpe Ratio**: >1.0 good, >2.0 excellent
- **Max Drawdown**: <10% conservative, <20% acceptable
- **Recovery Factor**: >2.0 good (return/drawdown ratio)
- **VaR**: Daily risk exposure at 95% confidence

### **Strategy Optimization**

#### **Parameter Tuning**
- **Position Size**: Adjust based on risk tolerance
- **Take Profit/Stop Loss**: Balance reward vs risk
- **Technical Indicators**: Optimize MA periods, RSI levels
- **Entry/Exit Rules**: Refine signal confirmation

#### **Performance Improvement**
- **Reduce Drawdown**: Tighter stop losses, better entry timing
- **Improve Win Rate**: Better signal filtering, confirmation
- **Increase Profit Factor**: Optimize reward/risk ratios
- **Enhance Sharpe**: Reduce volatility while maintaining returns

## Backtest Validation

### **Statistical Significance**
- **Minimum Trades**: Need 30+ trades for reliability
- **Time Period**: Test multiple periods (bull/bear/sideways)
- **Out-of-Sample**: Reserve recent data for validation
- **Walk-Forward**: Test on rolling time periods

### **Reality Checks**
- **Transaction Costs**: Account for trading fees
- **Slippage**: Real execution may differ from backtest
- **Market Impact**: Large orders may affect prices  
- **Overfitting**: Avoid over-optimizing to historical data

### **Data Quality**
- **Real vs Synthetic**: Prefer real data when available
- **Time Alignment**: Ensure proper timestamp handling
- **Corporate Actions**: Account for splits, dividends
- **Survivorship Bias**: Include delisted stocks in portfolio tests

## Limitations & Disclaimers

### **⚠️ Important Limitations**
1. **Past Performance**: Does not guarantee future results
2. **Market Conditions**: Strategies may perform differently in different market environments
3. **Data Availability**: Limited historical crypto data from Alpaca
4. **Synthetic Data**: When real data unavailable, synthetic data used for demonstration
5. **Execution Assumptions**: Perfect execution assumed (no slippage/fees)

### **🔍 Backtesting Best Practices**
1. **Multiple Timeframes**: Test different periods
2. **Parameter Sensitivity**: Test parameter variations
3. **Out-of-Sample Testing**: Reserve data for final validation
4. **Walk-Forward Analysis**: Rolling time window testing
5. **Reality Testing**: Account for real-world constraints

### **📊 Coming Enhancements**
- **Monte Carlo Simulation**: Randomized scenario testing
- **Multi-Timeframe Analysis**: Different bar intervals
- **Advanced Optimization**: Genetic algorithms for parameter tuning
- **Portfolio Backtest Completion**: Full portfolio strategy testing
- **Real-time Data Expansion**: More historical data sources

---

## API Reference

### **Backtest Endpoint**
```
POST /api/strategies/{strategy_id}/backtest
```

**Request Body:**
```json
{
  "days_back": 30,
  "initial_capital": 10000.0,
  "config": {
    // Strategy-specific configuration
  }
}
```

**Response:**
```json
{
  "strategy_type": "btc_scalping",
  "symbol": "BTC/USD", 
  "period": "30 days",
  "data_source": "real", // or "synthetic"
  "initial_capital": 10000.0,
  "final_capital": 10520.0,
  "total_return": 520.0,
  "total_return_pct": 5.2,
  "total_trades": 15,
  "win_rate": 66.7,
  "sharpe_ratio": 1.45,
  "max_drawdown": 3.2,
  "trades": [...],           // Last 20 trades
  "equity_curve": [...],     // Portfolio value over time
  "monthly_returns": [...],  // Month-by-month breakdown
  "risk_metrics": {...}      // Additional risk measures
}
```

The backtesting system provides comprehensive analysis to help you **validate strategies**, **optimize parameters**, and **understand risks** before deploying real capital! 🚀