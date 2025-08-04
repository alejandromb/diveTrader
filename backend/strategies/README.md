# DiveTrader Strategies 🏊‍♂️

This directory contains the automated trading strategies implemented in DiveTrader. Each strategy is designed to operate independently with its own configuration, risk management, and execution logic.

## Available Strategies

### 1. **BTC Scalping Strategy** ([`btc_scalping/`](./btc_scalping/))
AI-enhanced Bitcoin scalping strategy for short-term profits using technical analysis and machine learning.

### 2. **Portfolio Distributor Strategy** ([`portfolio_distributor/`](./portfolio_distributor/))
Automated dollar-cost averaging strategy that periodically invests in a diversified stock portfolio with rebalancing.

---

## Strategy Architecture

All strategies follow a common interface:

```python
class Strategy:
    def __init__(self, strategy_id, trading_service, db_session, config)
    def start()           # Initialize and start the strategy
    def stop()            # Stop strategy and close positions
    def run_iteration()   # Execute one strategy cycle
    def get_status()      # Get current strategy status
```

## Risk Management Integration

All strategies integrate with the **Risk Management System**:
- **Position Sizing**: Automatic calculation based on risk per trade
- **Drawdown Limits**: Stop trading when drawdown exceeds limits
- **Daily Loss Limits**: Halt trading if daily losses exceed threshold
- **Trade Validation**: Every trade is validated before execution

## Event Logging

Strategies automatically log events:
- **Strategy Lifecycle**: Start/stop events
- **Trade Checks**: Market analysis and signal generation
- **Order Execution**: Trade placement and fills
- **Risk Alerts**: Risk management warnings and stops
- **Performance Updates**: P&L and metrics tracking

View detailed logs through the **📋 Event Logs** button in the UI.

---

## Adding New Strategies

To add a new trading strategy:

1. **Create Strategy Class** in this directory
2. **Implement Required Methods**: `start()`, `stop()`, `run_iteration()`, `get_status()`
3. **Add to Strategy Types** in `database/models.py`
4. **Update Strategy Runner** in `services/strategy_runner.py`
5. **Add UI Configuration** in frontend components

## Configuration Format

Strategies are configured via JSON in the database:

```json
{
  "strategy_type": {
    "param1": "value1",
    "param2": "value2"
  },
  "risk_management": {
    "max_daily_loss": 5.0,
    "max_drawdown": 15.0
  }
}
```

## Testing & Backtesting

- **Paper Trading**: All strategies run in paper trading mode by default
- **Backtesting**: Historical performance testing available via API
- **Event Logs**: Comprehensive activity tracking for debugging
- **Risk Simulation**: Test risk management rules before live trading

---

## Strategy Performance Monitoring

Real-time monitoring includes:
- **ROI & P&L Tracking**
- **Win Rate & Trade Statistics**
- **Sharpe Ratio & Risk Metrics**
- **Drawdown Analysis**
- **Real-time Event Logs**

Access through the DiveTrader dashboard for complete strategy oversight.