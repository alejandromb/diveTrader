# DiveTrader - Claude Project Context

## Project Overview
A trading platform using Alpaca Markets API with multiple automated trading strategies.

## Main Goals
1. **BTC Scalping Strategy** - Automated Bitcoin scalping for short-term profits
2. **Portfolio Distributor** - Weekly automatic investment distributed across selected stock portfolios
3. **Paper Trading Testing** - Test strategies for weeks before live trading

## Current Architecture
- **Frontend**: React TypeScript with Vite (port 5173)
- **Backend**: FastAPI Python (Alpaca integration)
- **API**: Alpaca Markets Paper Trading API
- **Database**: SQLite for development

## Project Structure
```
diveTrader/
├── frontend/          # React TypeScript frontend
├── backend/           # FastAPI Python backend
├── strategies/        # Trading strategy implementations
│   ├── btc-scalping/  # Bitcoin scalping strategy
│   └── portfolio-distributor/  # Stock portfolio distribution
├── config/            # Configuration files
└── docs/              # Documentation
```

## Setup Status
✅ Git repository initialized and pushed to GitHub
✅ React frontend with Vite setup
✅ FastAPI backend with Alpaca integration
✅ BTC scalping strategy implementation
✅ Portfolio distributor strategy implementation
✅ Environment configuration (.env setup)
✅ Enhanced frontend trading dashboard with real Alpaca data
✅ Account info, positions, and trades panels with real-time updates
✅ Strategy management system (create, delete, configure)
✅ Real-time price tickers and trade analytics
✅ Risk management system with alerts and limits
✅ Development startup scripts

## API Configuration
- **Endpoint**: https://paper-api.alpaca.markets/v2
- **API Key**: Stored in backend/.env (PK0IA28FCW5BVDVYPWVW)
- **Secret Key**: Needs to be added to backend/.env

## Next Steps
1. ✅ Complete portfolio distributor strategy implementation
2. ✅ Build frontend dashboard for strategy monitoring
3. ✅ Implement real-time data feeds
4. ✅ Add comprehensive risk management
5. Add strategy backtesting capabilities
6. Create paper trading test environment
7. Add more advanced technical indicators
8. Implement portfolio optimization algorithms
9. Prepare for live trading transition

## Development Commands
**🚀 Quick Start (Recommended):**
- Start everything: `npm run dev` or `./start-dev.sh`
- Windows: `start-dev.bat`

**Individual Commands:**
- Frontend only: `cd frontend && npm run dev`
- Backend only: `cd backend && python main.py`
- Install all deps: `npm run install-all`
- Build frontend: `npm run build`

**Setup Requirements:**
1. Backend virtual env: `cd backend && python -m venv venv`
2. Install backend deps: `source venv/bin/activate && pip install -r requirements.txt`
3. Create backend/.env with Alpaca API keys
4. Install frontend deps: `cd frontend && npm install`

## Repository
- GitHub: https://github.com/alejandromb/diveTrader
- Branch: main
- Status: All code committed and pushed

## Current Implementation Details

### Frontend Features
- **Real-time Dashboard**: 3-column layout with live data updates
- **Strategy Management**: Create, configure, start/stop, delete strategies
- **Real-time Price Tickers**: Live market data from Alpaca API
- **Trade Analytics**: Enhanced trade filtering and performance metrics
- **Risk Management Panel**: Live risk alerts and configurable limits
- **Position Tracking**: Real-time position monitoring with P&L

### Backend Services
- **Trading Service**: Alpaca API integration for live market data
- **Strategy Engines**: BTC scalping and portfolio distributor strategies
- **Risk Management**: Comprehensive risk rules and position sizing
- **Performance Tracking**: Real-time metrics and analytics
- **Database Models**: SQLite with strategy, position, trade, and performance tables

### Risk Management Features
- Position sizing based on risk per trade and stop losses
- Drawdown monitoring with configurable limits
- Daily loss limits with automatic trade blocking
- Portfolio concentration analysis
- Real-time risk alerts with severity levels
- Configurable risk limits per strategy

### Database Structure
- **strategies**: Strategy configurations and status
- **positions**: Current positions with real-time market values
- **trades**: Trade history with execution details
- **performance_metrics**: Daily performance tracking
- Database location: `backend/divetrader.db` (SQLite)

### API Endpoints
- `/api/strategies/` - Strategy CRUD operations
- `/api/trading/` - Trading operations and market data
- `/api/risk/` - Risk management and validation
- Paper trading mode enabled by default