# DiveTrader

A trading platform using Alpaca Markets API with multiple strategies.

## Project Structure

- `backend/` - API server and core trading logic
- `frontend/` - Web interface for monitoring and configuration
- `strategies/` - Trading strategy implementations
  - `btc-scalping/` - Bitcoin scalping strategy
  - `portfolio-distributor/` - Weekly portfolio distribution strategy
- `config/` - Configuration files
- `docs/` - Documentation

## Strategies

### 1. BTC Scalping
High-frequency Bitcoin trading strategy for short-term profits.

### 2. Portfolio Distributor
Weekly investment strategy that automatically distributes funds across a diversified stock portfolio.

## Getting Started

1. Set up Alpaca Markets API credentials
2. Install dependencies
3. Configure strategies
4. Run the application