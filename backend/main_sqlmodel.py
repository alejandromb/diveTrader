"""
FastAPI Application with SQLModel Integration
Type-safe database models and auto-generated schemas
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database.sqlmodel_database import init_database
from api.strategies import router as legacy_strategies_router
from api.trading import router as trading_router
from api.risk_management import router as risk_router
from api.strategy_events import router as events_router
from api.strategy_settings import router as legacy_settings_router
from api.typed_strategies import router as typed_strategies_router
from services.typed_strategy_runner import typed_strategy_runner
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
        logging.FileHandler('typed_strategy_runner.log')
    ]
)

# Initialize SQLModel database
init_database()

app = FastAPI(
    title="DiveTrader API v2 (SQLModel)", 
    version="2.0.0",
    description="Type-safe trading platform API with auto-generated schemas"
)

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
app.include_router(typed_strategies_router)  # New type-safe endpoints
app.include_router(legacy_strategies_router)  # Legacy endpoints for compatibility
app.include_router(trading_router)
app.include_router(risk_router)
app.include_router(events_router)
app.include_router(legacy_settings_router)  # Legacy settings for backward compatibility

@app.get("/")
async def root():
    return {
        "message": "DiveTrader API v2 with SQLModel",
        "version": "2.0.0",
        "features": [
            "Type-safe database models",
            "Auto-generated API schemas", 
            "Built-in validation",
            "TypeScript type generation",
            "Typed strategy runners"
        ]
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "paper_trading": True,
        "database": "SQLModel",
        "running_strategies": len(typed_strategy_runner.get_running_strategies())
    }

@app.get("/api/info")
async def api_info():
    """API information and available endpoints"""
    return {
        "version": "2.0.0",
        "database": "SQLModel (Type-safe)",
        "features": {
            "typed_strategies": "Full type safety with validation",
            "auto_schemas": "Automatic OpenAPI schema generation", 
            "typescript_types": "Generate TypeScript types from Python models",
            "legacy_compatibility": "Backward compatible with v1 endpoints"
        },
        "endpoints": {
            "typed_strategies": "/api/v2/strategies/*",
            "legacy_strategies": "/api/strategies/*", 
            "trading": "/api/trading/*",
            "risk": "/api/risk/*",
            "events": "/api/events/*"
        },
        "running_strategies": typed_strategy_runner.get_running_strategies()
    }

@app.on_event("startup")
async def startup_event():
    """Initialize typed strategy runner on startup"""
    logger = logging.getLogger(__name__)
    logger.info("🚀 Starting DiveTrader API v2 with SQLModel...")
    logger.info("✅ Type-safe database models loaded")
    logger.info("✅ Auto-generated API schemas available")
    logger.info("✅ Typed strategy runner ready")
    
    # The typed strategy runner manages its own threads
    # Strategies will be started when requested via API calls

@app.on_event("shutdown") 
async def shutdown_event():
    """Clean shutdown of typed strategy runner"""
    logger = logging.getLogger(__name__)
    logger.info("🛑 Shutting down DiveTrader API v2...")
    
    # Stop all running strategies
    typed_strategy_runner.shutdown()
    
    logger.info("✅ Typed strategy runner shutdown complete")

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting DiveTrader API v2 with SQLModel...")
    print("📊 Type-safe database models")
    print("🔧 Auto-generated API schemas")
    print("🎯 Built-in validation")
    print("📝 TypeScript type generation")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)