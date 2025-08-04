# BTC Scalping Strategy ₿

**AI-Enhanced Bitcoin Scalping for Short-Term Profits**

## Overview

The BTC Scalping Strategy is an automated trading system that combines traditional technical analysis with AI-powered market analysis to capture short-term price movements in Bitcoin. It operates on 1-minute timeframes with configurable risk management and intelligent signal generation.

## Strategy Features

### 🤖 **AI-Enhanced Analysis**
- **Machine Learning Integration**: Uses AI analysis service for market predictions
- **Confidence-Based Decisions**: Only acts on high-confidence AI signals  
- **Signal Combination**: Intelligently combines AI and technical indicators
- **Fallback Protection**: Falls back to traditional analysis if AI fails

### 📊 **Technical Analysis**
- **Moving Average Crossover**: Short MA (3 periods) vs Long MA (5 periods)
- **Volume Filtering**: Minimum volume requirements for signal validation
- **Price Action**: Confirmation using current price vs moving averages
- **Trend Following**: Buys when short MA crosses above long MA

### ⚡ **Scalping Features**
- **Fast Execution**: 1-minute bar analysis for quick decisions
- **Small Profits**: Targets 0.2% gains with 0.1% stop losses
- **Rapid Positions**: Quick entry and exit for profit capture
- **Volume Requirements**: Ensures adequate liquidity before trading

## Configuration Parameters

```json
{
  "btc_scalping": {
    "position_size": 0.001,           // BTC amount per trade
    "take_profit_pct": 0.002,         // 0.2% take profit
    "stop_loss_pct": 0.001,           // 0.1% stop loss
    "lookback_periods": 10,           // Bars for analysis
    "short_ma_periods": 3,            // Fast moving average
    "long_ma_periods": 5,             // Slow moving average
    "min_volume": 1000,               // Minimum volume filter
    "max_positions": 1,               // Maximum concurrent positions
    
    // AI Configuration
    "use_ai_analysis": true,          // Enable AI analysis
    "ai_confidence_threshold": 0.6,   // Minimum AI confidence
    "combine_ai_with_technical": true, // Require both to agree
    "ai_override_technical": false    // Allow AI to override TA
  }
}
```

## Trading Logic

### **Entry Conditions**
1. **Technical Signal**: Short MA crosses above Long MA
2. **Price Confirmation**: Current price > Short MA
3. **Volume Check**: Volume > minimum threshold  
4. **AI Agreement**: AI signal matches technical (if enabled)
5. **Position Limit**: No existing positions
6. **Timing**: No signals in last 5 minutes (prevents spam)

### **Exit Conditions**
- **Take Profit**: Price reaches +0.2% from entry
- **Stop Loss**: Price falls to -0.1% from entry
- **Strategy Stop**: Manual stop closes all positions

### **Risk Management**
- **Fixed Position Size**: 0.001 BTC per trade (configurable)
- **Automatic Stops**: Built-in stop loss and take profit
- **Position Limits**: Maximum 1 open position
- **Capital Protection**: Uses risk management service validation

## AI Integration Details

### **Analysis Process**
1. **Data Preparation**: Converts price bars to AI service format
2. **Technical Indicators**: Calculates indicators for AI context
3. **Market Analysis**: AI analyzes market conditions and trends
4. **Signal Generation**: AI provides BUY/SELL/HOLD with confidence
5. **Signal Combination**: Merges AI and technical analysis

### **AI Decision Logic**
- **Low Confidence** (<0.6): Use traditional technical analysis
- **High Confidence** (>0.8): AI can override if enabled
- **Agreement Mode**: Both AI and TA must agree for trades
- **Fallback**: Uses traditional analysis if AI fails

## Performance Characteristics

### **Strengths**
- **Quick Profits**: Targets small, frequent gains
- **AI Enhancement**: Improved signal accuracy
- **Risk Controlled**: Fixed stop losses and position limits
- **Liquid Market**: Bitcoin provides excellent liquidity

### **Limitations**
- **Market Dependent**: Works best in trending markets
- **Transaction Costs**: Frequent trading may impact profits
- **Whipsaws**: Can generate false signals in choppy markets
- **AI Dependency**: Relies on AI service availability

## Monitoring & Events

### **Event Log Types**
- `trade_check`: Market analysis and signal generation
- `signal_generated`: AI or technical signals with confidence
- `order_placed`: Trade execution details
- `order_filled`: Position entry/exit confirmations
- `risk_alert`: Risk management warnings
- `performance_update`: P&L and metrics updates

### **Key Metrics**
- **Win Rate**: Percentage of profitable trades
- **Average Profit**: Mean profit per successful trade
- **Average Loss**: Mean loss per failed trade
- **Sharpe Ratio**: Risk-adjusted returns
- **Max Drawdown**: Largest peak-to-trough decline

## Recommended Settings

### **Conservative** (Lower Risk)
```json
{
  "position_size": 0.0005,
  "take_profit_pct": 0.001,
  "stop_loss_pct": 0.0005,
  "ai_confidence_threshold": 0.8
}
```

### **Aggressive** (Higher Risk)
```json
{
  "position_size": 0.002,
  "take_profit_pct": 0.003,
  "stop_loss_pct": 0.002,
  "ai_confidence_threshold": 0.5
}
```

## Implementation Notes

### **Market Data**
- **Source**: Alpaca Crypto API
- **Timeframe**: 1-minute bars
- **Symbol Handling**: Supports BTC/USD, BTCUSD formats
- **Data Window**: 2-hour lookback for analysis

### **Error Handling**
- **Data Failures**: Graceful fallback when market data unavailable
- **AI Failures**: Falls back to technical analysis
- **Order Failures**: Comprehensive error logging and alerts
- **Position Tracking**: Maintains accurate position state

### **Performance Optimization**
- **Efficient Data Access**: Minimizes API calls
- **Memory Management**: Cleans up old position data
- **Connection Pooling**: Reuses database connections
- **Async Operations**: Non-blocking market data fetching

---

## Usage Example

```python
# Create strategy instance
strategy = BTCScalpingStrategy(
    strategy_id=1,
    trading_service=trading_service,
    performance_service=performance_service,
    db_session=db,
    config=json.dumps(config)
)

# Start the strategy
strategy.start()

# Run trading loop (handled by strategy runner)
while strategy.is_running:
    strategy.run_iteration()
    time.sleep(60)  # 1-minute intervals

# Stop and cleanup
strategy.stop()
```

This strategy is ideal for traders seeking **automated Bitcoin profits** with **AI-enhanced decision making** and **controlled risk exposure**.