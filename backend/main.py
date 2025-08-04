from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database.database import create_tables
from api.strategies import router as strategies_router
from api.trading import router as trading_router
import os
from dotenv import load_dotenv

load_dotenv()

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

@app.get("/")
async def root():
    return {"message": "DiveTrader API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "paper_trading": True}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)