# Portfolio Distributor Strategy 📊

**Automated Dollar-Cost Averaging with Portfolio Rebalancing**

## Overview

The Portfolio Distributor Strategy implements systematic investment using dollar-cost averaging (DCA) across a diversified portfolio of stocks. It automatically invests fixed amounts at regular intervals and maintains target allocation percentages through intelligent rebalancing.

## Strategy Features

### 💰 **Dollar-Cost Averaging**
- **Regular Investments**: Weekly or monthly investment schedule
- **Fixed Amounts**: Consistent investment regardless of market conditions
- **Automatic Execution**: No manual intervention required
- **Market Timing**: Reduces impact of market volatility

### 🎯 **Portfolio Management**
- **Diversification**: Spreads investments across multiple stocks
- **Allocation Weighting**: Customizable percentage allocations
- **Automatic Rebalancing**: Maintains target percentages
- **Fractional Shares**: Maximizes investment efficiency

### ⚖️ **Rebalancing Logic**
- **Threshold-Based**: Rebalances when allocations drift >5%
- **Scheduled Checks**: Daily analysis at market close
- **Smart Timing**: Avoids unnecessary frequent rebalancing
- **Cost Optimization**: Minimizes transaction costs

## Configuration Parameters

```json
{
  "portfolio_distributor": {
    "symbols": ["AAPL", "MSFT", "GOOGL", "TSLA", "SPY"],
    "allocation_weights": {
      "AAPL": 25.0,     // 25% allocation
      "MSFT": 25.0,     // 25% allocation  
      "GOOGL": 20.0,    // 20% allocation
      "TSLA": 15.0,     // 15% allocation
      "SPY": 15.0       // 15% allocation (total must equal 100%)
    },
    "investment_frequency": "weekly",    // "weekly" or "monthly"
    "investment_amount": 1000,           // Amount to invest each period
    "rebalance_threshold": 5.0,          // % deviation before rebalancing
    "min_investment_per_stock": 1.0      // Minimum $ per stock per investment
  }
}
```

## Investment Process

### **Investment Schedule**
1. **Weekly**: Every Monday at market open
2. **Monthly**: First trading day of each month
3. **Custom**: Configurable frequency support

### **Investment Execution**
1. **Capital Check**: Ensures sufficient available capital
2. **Price Fetching**: Gets current market prices for all symbols
3. **Allocation Calculation**: Determines investment per stock based on weights
4. **Order Placement**: Executes buy orders for calculated quantities
5. **Schedule Update**: Sets next investment date

### **Rebalancing Process**
1. **Portfolio Analysis**: Calculates current allocation percentages
2. **Deviation Check**: Compares actual vs target allocations
3. **Threshold Analysis**: Identifies stocks needing rebalancing
4. **Rebalance Execution**: Buys/sells to restore target percentages
5. **Cost Analysis**: Ensures rebalancing benefits outweigh costs

## Portfolio Management

### **Default Portfolio**
- **AAPL** (Apple): 25% - Technology leader
- **MSFT** (Microsoft): 25% - Cloud computing
- **GOOGL** (Google): 20% - Digital advertising
- **TSLA** (Tesla): 15% - Electric vehicles
- **SPY** (S&P 500 ETF): 15% - Market diversification

### **Allocation Strategies**

#### **Conservative Growth**
```json
{
  "SPY": 40.0,    // S&P 500 ETF
  "VTI": 30.0,    // Total Stock Market
  "AAPL": 15.0,   // Blue chip tech
  "MSFT": 15.0    // Stable growth
}
```

#### **Tech-Heavy Growth**
```json
{
  "AAPL": 30.0,   // Apple
  "MSFT": 25.0,   // Microsoft  
  "GOOGL": 20.0,  // Google
  "NVDA": 15.0,   // NVIDIA
  "TSLA": 10.0    // Tesla
}
```

#### **Diversified Balanced**
```json
{
  "SPY": 25.0,    // Large cap
  "QQQ": 20.0,    // Tech ETF
  "AAPL": 15.0,   // Individual tech
  "MSFT": 15.0,   // Individual tech
  "VWO": 10.0,    // Emerging markets
  "VEA": 10.0,    // Developed international
  "VTEB": 5.0     // Tax-exempt bonds
}
```

## Risk Management Integration

### **Position Limits**
- **Maximum Allocation**: No single stock >40% of portfolio
- **Minimum Investment**: Skip positions <$1 to avoid fees
- **Capital Preservation**: Never invest more than available capital
- **Rebalancing Limits**: Maximum 20% portfolio turnover per rebalance

### **Risk Monitoring**
- **Concentration Risk**: Alerts if portfolio becomes overconcentrated
- **Performance Tracking**: Monitors relative performance vs benchmarks
- **Drawdown Analysis**: Tracks portfolio drawdown vs individual stocks
- **Correlation Analysis**: Monitors correlation between holdings

## Event Logging

### **Investment Events**
- `portfolio_investment`: Scheduled investment execution
- `symbol_purchase`: Individual stock purchase details
- `allocation_update`: Portfolio allocation changes
- `rebalancing_check`: Rebalancing analysis results

### **Management Events**
- `portfolio_rebalance`: Rebalancing execution
- `allocation_drift`: When allocations exceed thresholds
- `capital_insufficient`: When investment amount exceeds available capital
- `market_data_error`: When price data is unavailable

## Performance Characteristics

### **Advantages**
- **Volatility Reduction**: DCA reduces market timing risk
- **Automatic Discipline**: Removes emotional investment decisions
- **Diversification**: Spreads risk across multiple assets
- **Compound Growth**: Reinvests dividends and maintains growth trajectory

### **Considerations**
- **Bull Market Lag**: May underperform lump-sum in rising markets
- **Transaction Costs**: Frequent small trades may incur fees
- **Cash Drag**: Maintains cash reserves for regular investments
- **Market Correlation**: All stocks may decline together in market downturns

## Monitoring & Analytics

### **Key Metrics**
- **Portfolio Return**: Total portfolio performance vs benchmarks
- **Allocation Drift**: Current vs target allocation percentages
- **Investment Consistency**: Tracks successful investment executions
- **Rebalancing Frequency**: Number and effectiveness of rebalances
- **Cost Analysis**: Transaction costs as % of portfolio value

### **Performance Tracking**
- **Total Return**: Capital gains + dividends
- **Sharpe Ratio**: Risk-adjusted returns
- **Beta Analysis**: Portfolio volatility vs market
- **Alpha Generation**: Excess returns vs benchmark
- **Maximum Drawdown**: Largest portfolio decline

## Implementation Features

### **Scheduling System**
- **Next Investment Date**: Automatically calculated based on frequency
- **Market Calendar**: Respects trading holidays and weekends
- **Time Zone Handling**: Handles market hours correctly
- **Retry Logic**: Handles temporary market data or execution failures

### **Order Management**
- **Whole Share Purchase**: Calculates integer share quantities
- **Price Optimization**: Uses current market prices for calculations
- **Order Validation**: Ensures orders meet minimum requirements
- **Execution Tracking**: Monitors order fills and updates positions

### **Database Integration**
- **Portfolio Records**: Stores allocation weights and schedules
- **Position Tracking**: Maintains accurate position quantities
- **Trade History**: Complete record of all investment transactions
- **Performance History**: Daily portfolio valuation and metrics

---

## Usage Example

```python
# Initialize portfolio distributor
distributor = PortfolioDistributorStrategy(trading_service)

# Initialize strategy with configuration
success = distributor.initialize_strategy(strategy, db)

# Check if investment is due
if distributor.should_invest_today(strategy_id, db):
    # Execute scheduled investment
    result = distributor.execute_investment(strategy_id, db)
    
# Check for rebalancing needs
if distributor.check_rebalancing_needed(strategy_id, db):
    # Trigger rebalancing (implementation pending)
    pass

# Run complete strategy cycle
result = distributor.run_strategy(strategy_id, db)
```

## Best Practices

### **Portfolio Construction**
- **Diversify Across Sectors**: Include technology, healthcare, finance, etc.
- **Include ETFs**: Add broad market exposure with SPY, QQQ, etc.
- **Consider International**: Add VEA (developed) or VWO (emerging) markets
- **Balance Growth/Value**: Mix growth stocks with value stocks

### **Allocation Management**
- **Start Conservative**: Begin with broader ETFs, add individual stocks gradually
- **Regular Review**: Reassess allocations quarterly or semi-annually
- **Rebalancing Discipline**: Don't let any position exceed 30-40% of portfolio
- **Tax Efficiency**: Consider tax implications of frequent rebalancing

This strategy is perfect for **long-term wealth building** through **disciplined, automated investing** with **professional portfolio management** principles.