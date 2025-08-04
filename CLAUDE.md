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
✅ BTC scalping strategy skeleton implemented
✅ Environment configuration (.env setup)
✅ Enhanced frontend trading dashboard with Alpaca data
✅ Account info, positions, and trades panels
✅ Development startup scripts
⏸️ Portfolio distributor strategy (pending)

## API Configuration
- **Endpoint**: https://paper-api.alpaca.markets/v2
- **API Key**: Stored in backend/.env (PK0IA28FCW5BVDVYPWVW)
- **Secret Key**: Needs to be added to backend/.env

## Next Steps
1. Complete portfolio distributor strategy implementation
2. Build frontend dashboard for strategy monitoring
3. Implement real-time data feeds
4. Add strategy backtesting capabilities
5. Create paper trading test environment
6. Prepare for live trading transition

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
- BTC scalping uses momentum indicators with configurable risk management
- Backend provides REST API endpoints for strategy control
- Paper trading integration ready for testing
- CORS enabled for frontend-backend communication