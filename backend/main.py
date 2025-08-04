from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database.database import create_tables
from api.strategies import router as strategies_router
from api.trading import router as trading_router
from api.risk_management import router as risk_router
from api.strategy_events import router as events_router
from services.strategy_runner import strategy_runner
import os
import asyncio
import threading
import logging
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('strategy_runner.log')
    ]
)

# Create database tables
create_tables()

app = FastAPI(title="DiveTrader API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://localhost:4173",  # Vite preview server
        "http://localhost:3000",  # Common React port
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(strategies_router)
app.include_router(trading_router)
app.include_router(risk_router)
app.include_router(events_router)

@app.get("/")
async def root():
    return {"message": "DiveTrader API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "paper_trading": True}

@app.on_event("startup")
async def startup_event():
    """Initialize strategy runner on startup"""
    import logging
    logger = logging.getLogger(__name__)
    logger.info("Starting strategy runner...")
    
    # Strategy runner manages its own threads, no need to start anything here
    # It will start strategies when requested via API calls
    logger.info("Strategy runner ready")

@app.on_event("shutdown") 
async def shutdown_event():
    """Clean shutdown of strategy runner"""
    import logging
    logger = logging.getLogger(__name__)
    logger.info("Shutting down strategy runner...")
    
    # Stop all running strategies
    for strategy_id in list(strategy_runner.running_strategies.keys()):
        strategy_runner.stop_strategy(strategy_id)
    
    logger.info("Strategy runner shutdown complete")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)