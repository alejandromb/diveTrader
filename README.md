# DiveTrader

A trading platform using Alpaca Markets API with multiple automated trading strategies and performance visualization.

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+
- Alpaca Markets Paper Trading Account

### 1. Backend Setup
```bash
cd backend

# Install Python dependencies
pip install -r requirements.txt

# Add your Alpaca API credentials to .env
ALPACA_SECRET_KEY=your_secret_key_here

# Start the API server
python main.py
```
Backend runs on: http://localhost:8000

### 2. Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```
Frontend runs on: http://localhost:5173

### 3. Test the API
```bash
# Check API health
curl http://localhost:8000/health

# Get account info
curl http://localhost:8000/api/trading/account

# Create a strategy
curl -X POST http://localhost:8000/api/strategies/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My BTC Strategy",
    "strategy_type": "btc_scalping",
    "initial_capital": 10000.0
  }'
```

## 📊 Architecture

**Frontend (React + TypeScript)**
- Real-time performance dashboards
- Strategy management interface
- ROI visualization with charts

**Backend (FastAPI + PostgreSQL)**
- Internal API middleware
- Trade execution & position tracking
- Performance metrics calculation
- Alpaca Markets integration

**Database Schema**
- Strategies, Positions, Trades
- Daily performance metrics
- Portfolio allocations

## 🔧 API Endpoints

### Strategies
- `GET /api/strategies/` - List all strategies
- `POST /api/strategies/` - Create strategy
- `GET /api/strategies/{id}/performance` - Performance metrics
- `GET /api/strategies/{id}/daily-metrics` - Chart data

### Trading
- `GET /api/trading/account` - Account info
- `POST /api/trading/order` - Place order
- `GET /api/trading/positions/{strategy_id}` - Strategy positions

## 📈 Features

✅ **Paper Trading Integration** - Safe testing environment  
✅ **Performance Tracking** - ROI, Sharpe ratio, win rates  
✅ **Position Management** - Real-time sync with Alpaca  
✅ **Strategy Management** - Start/stop multiple strategies  
⏸️ **Visual Dashboard** - Coming next  
⏸️ **BTC Scalping Strategy** - Implementation ready  
⏸️ **Portfolio Distributor** - Weekly investment automation  

## 🔐 Configuration

Update `backend/.env` with your credentials:
```env
ALPACA_API_KEY=PK0IA28FCW5BVDVYPWVW
ALPACA_SECRET_KEY=your_secret_key_here
DATABASE_URL=postgresql://postgres:password@localhost:5432/divetrader
POSTGRES_AVAILABLE=false  # Set to true if you have PostgreSQL
```

## 🎯 Trading Strategies

### BTC Scalping
- Momentum-based entry signals
- Configurable risk management
- Take-profit/stop-loss automation

### Portfolio Distributor  
- Weekly investment schedule
- Multi-stock diversification
- Automatic rebalancing

## 🚀 AWS Deployment Ready
- PostgreSQL database schema
- Environment-based configuration
- Scalable FastAPI architecture