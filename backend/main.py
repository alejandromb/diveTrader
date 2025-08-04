from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.live import StockDataStream
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="DiveTrader API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Alpaca client setup for paper trading
trading_client = TradingClient(
    api_key=os.getenv("ALPACA_API_KEY"),
    secret_key=os.getenv("ALPACA_SECRET_KEY"),
    paper=True  # Paper trading
)

data_client = StockHistoricalDataClient(
    api_key=os.getenv("ALPACA_API_KEY"),
    secret_key=os.getenv("ALPACA_SECRET_KEY")
)

@app.get("/")
async def root():
    return {"message": "DiveTrader API is running"}

@app.get("/account")
async def get_account():
    """Get account information"""
    try:
        account = trading_client.get_account()
        return {
            "account_number": account.account_number,
            "buying_power": float(account.buying_power),
            "cash": float(account.cash),
            "portfolio_value": float(account.portfolio_value),
            "status": account.status
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/positions")
async def get_positions():
    """Get all positions"""
    try:
        positions = trading_client.get_all_positions()
        return [
            {
                "symbol": pos.symbol,
                "qty": float(pos.qty),
                "market_value": float(pos.market_value),
                "cost_basis": float(pos.cost_basis),
                "unrealized_pl": float(pos.unrealized_pl),
                "unrealized_plpc": float(pos.unrealized_plpc)
            }
            for pos in positions
        ]
    except Exception as e:
        return {"error": str(e)}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "paper_trading": True}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)