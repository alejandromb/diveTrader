# Trading Strategies - Important Considerations

## Strategy Types

### BTC Scalping Strategy (`/backend/strategies/btc_scalping_strategy.py`)
- **Asset Type**: Cryptocurrency (BTC/USD)
- **Execution**: Active - runs every 60 seconds when enabled
- **Risk Level**: Medium-High (scalping with tight stops)
- **Day Trading**: ✅ Safe - Crypto not subject to PDT rules

### Portfolio Distributor Strategy (Planned)
- **Asset Type**: US Stocks
- **Execution**: Weekly distribution
- **Risk Level**: Low-Medium (diversified positions)
- **Day Trading**: ⚠️ **CRITICAL PDT CONSIDERATIONS**

## ⚠️ CRITICAL: Pattern Day Trading (PDT) Rules

### What is PDT?
- **Definition**: Making 4+ day trades within 5 business days
- **Day Trade**: Buy and sell (or sell and buy) the same stock on the same day
- **Account Requirement**: Must maintain $25,000+ equity to day trade freely
- **Current Account**: $2,090 (BELOW PDT minimum)

### PDT Rule Compliance for Stock Strategies

#### ✅ SAFE Practices:
- **Hold positions overnight** - No same-day buy/sell
- **Weekly/monthly rebalancing** - Space trades by days
- **Position sizing** - Fewer, larger positions vs many small trades
- **Buy and hold approach** - Avoid frequent trading

#### ❌ AVOID These Actions:
- Same-day buy/sell of ANY stock
- Frequent intraday position changes
- Scalping stocks (only crypto is safe for this)
- More than 3 day trades in 5 business days

### Implementation Guidelines

#### Portfolio Distributor Strategy MUST:
1. **Weekly Execution Only** - Run once per week maximum
2. **Hold Period Enforcement** - No selling positions for minimum 1 day
3. **Trade Counting** - Track day trades to stay under 3 per 5-day period
4. **Position Management** - Close positions only after overnight hold
5. **Emergency Override** - Only allow same-day exit for risk management (< -5% loss)

#### Code Requirements:
```python
# Add to all stock strategies:
def validate_day_trade_compliance(self, symbol: str, action: str):
    # Check if action would create a day trade
    # Prevent execution if it would violate PDT rules
    pass

def enforce_holding_period(self, position):
    # Ensure minimum 1-day hold before allowing exit
    pass
```

## Current Strategy Status

### BTC Scalping ✅ ACTIVE
- **Capital**: $2,090 (synced with Alpaca)
- **Execution**: Every 60 seconds
- **PDT Risk**: None (crypto exempt)
- **AI Analysis**: Enabled (fallback mode)

### Portfolio Distributor 🚧 NOT IMPLEMENTED
- **Status**: Planned
- **Priority**: Implement PDT compliance FIRST
- **Execution**: Weekly only
- **PDT Risk**: HIGH if not implemented correctly

## Safety Features

1. **Account Monitoring**: Real-time sync with Alpaca account balance
2. **Position Limits**: Max 1 position for BTC strategy
3. **Risk Management**: Stop losses and take profits enforced
4. **Paper Trading**: All trading currently in paper mode
5. **Logging**: Comprehensive trade and decision logging

## Running Safely

Yes, you can leave BTC scalping running - it's designed to:
- Use conservative position sizing (0.001 BTC ≈ $43)
- Implement strict stop losses (0.1%) and take profits (0.2%)  
- Only trade crypto (no PDT risk)
- Run in paper trading mode
- Auto-sync with your account balance

**For stock strategies: DO NOT enable until PDT compliance is implemented!**