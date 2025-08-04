from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.database import get_db
from services.trading_service import TradingService
from alpaca.trading.enums import OrderSide
from pydantic import BaseModel
from typing import List

router = APIRouter(prefix="/api/trading", tags=["trading"])
trading_service = TradingService()

class OrderRequest(BaseModel):
    strategy_id: int
    symbol: str
    side: str  # "buy" or "sell"
    quantity: float

class TradeResponse(BaseModel):
    id: int
    strategy_id: int
    symbol: str
    side: str
    quantity: float
    price: float
    status: str
    created_at: str

@router.get("/account")
async def get_account_info():
    """Get Alpaca account information"""
    try:
        return trading_service.get_account_info()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/order")
async def place_order(order: OrderRequest, db: Session = Depends(get_db)):
    """Place a trading order"""
    try:
        # Convert string to OrderSide enum
        side = OrderSide.BUY if order.side.lower() == "buy" else OrderSide.SELL
        
        trade = trading_service.place_order(
            strategy_id=order.strategy_id,
            symbol=order.symbol,
            side=side,
            quantity=order.quantity,
            db=db
        )
        
        return TradeResponse(
            id=trade.id,
            strategy_id=trade.strategy_id,
            symbol=trade.symbol,
            side=trade.side,
            quantity=trade.quantity,
            price=trade.price,
            status=trade.status,
            created_at=trade.created_at.isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/positions/{strategy_id}")
async def get_strategy_positions(strategy_id: int, db: Session = Depends(get_db)):
    """Get all positions for a specific strategy"""
    try:
        # First sync positions from Alpaca
        trading_service.update_positions(strategy_id, db)
        
        # Then return from database
        from database.models import Position
        positions = db.query(Position).filter(Position.strategy_id == strategy_id).all()
        
        return [
            {
                "id": pos.id,
                "symbol": pos.symbol,
                "quantity": pos.quantity,
                "avg_price": pos.avg_price,
                "current_price": pos.current_price,
                "market_value": pos.market_value,
                "unrealized_pnl": pos.unrealized_pnl,
                "side": pos.side,
                "opened_at": pos.opened_at.isoformat()
            }
            for pos in positions
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/trades/{strategy_id}")
async def get_strategy_trades(strategy_id: int, db: Session = Depends(get_db)):
    """Get all trades for a specific strategy"""
    try:
        from database.models import Trade
        trades = db.query(Trade).filter(
            Trade.strategy_id == strategy_id
        ).order_by(Trade.created_at.desc()).limit(100).all()
        
        return [
            {
                "id": trade.id,
                "symbol": trade.symbol,
                "side": trade.side,
                "quantity": trade.quantity,
                "price": trade.price,
                "commission": trade.commission,
                "realized_pnl": trade.realized_pnl,
                "status": trade.status,
                "executed_at": trade.executed_at.isoformat() if trade.executed_at else None,
                "created_at": trade.created_at.isoformat()
            }
            for trade in trades
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/market-data/{symbol}")
async def get_market_data(symbol: str, timeframe: str = "1Day", limit: int = 100):
    """Get historical market data for a symbol"""
    try:
        return trading_service.get_market_data(symbol, timeframe, limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))