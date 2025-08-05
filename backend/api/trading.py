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

class ManualOrderRequest(BaseModel):
    symbol: str
    side: str  # "buy" or "sell"
    quantity: float = None  # Number of shares (can be fractional)
    notional: float = None  # Dollar amount for fractional share purchases
    type: str = "market"  # "market" or "limit"
    time_in_force: str = "day"  # "day" or "gtc"
    limit_price: float = None

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

@router.get("/quotes")
async def get_latest_quotes(symbols: str):
    """Get latest quotes for multiple symbols (comma-separated)"""
    try:
        symbol_list = [s.strip() for s in symbols.split(',')]
        return trading_service.get_latest_quotes(symbol_list)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Manual Trading Endpoints

@router.get("/positions")
async def get_all_positions(db: Session = Depends(get_db)):
    """Get all positions across all strategies for manual trading"""
    try:
        # Get positions directly from Alpaca
        alpaca_positions = trading_service.get_alpaca_positions()
        
        positions = []
        for pos in alpaca_positions:
            positions.append({
                "symbol": pos.symbol,
                "quantity": float(pos.qty),
                "avg_price": float(pos.avg_entry_price),
                "current_price": float(pos.market_value) / float(pos.qty) if float(pos.qty) != 0 else 0,
                "market_value": float(pos.market_value),
                "unrealized_pnl": float(pos.unrealized_pl),
                "unrealized_pnl_percent": float(pos.unrealized_plpc) * 100,
                "side": "long" if float(pos.qty) > 0 else "short"
            })
        
        return positions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/orders")
async def place_manual_order(order: ManualOrderRequest):
    """Place a manual trading order (not tied to any strategy)"""
    try:
        result = trading_service.place_manual_order(
            symbol=order.symbol,
            side=order.side,
            quantity=order.quantity,
            notional=order.notional,
            order_type=order.type,
            time_in_force=order.time_in_force,
            limit_price=order.limit_price
        )
        order_description = f"${order.notional} of {order.symbol}" if order.notional else f"{order.quantity} shares of {order.symbol}"
        return {
            "message": f"{order.side.upper()} order placed for {order_description}",
            "order_id": result.id if hasattr(result, 'id') else None,
            "status": "submitted"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/quote/{symbol}")
async def get_single_quote(symbol: str):
    """Get a single stock quote with formatted data"""
    try:
        quotes = trading_service.get_latest_quotes([symbol.upper()])
        quote_data = quotes.get(symbol.upper())
        
        if not quote_data:
            raise HTTPException(status_code=404, detail=f"Quote not found for {symbol}")
        
        # Get additional market data if available
        try:
            bars = trading_service.get_market_data(symbol.upper(), "1Day", 2)
            prev_close = bars[-2]['close'] if len(bars) >= 2 else quote_data.get('ask_price', 0)
            current_price = quote_data.get('ask_price', quote_data.get('bid_price', 0))
            change = current_price - prev_close
            change_percent = (change / prev_close * 100) if prev_close > 0 else 0
        except:
            current_price = quote_data.get('ask_price', quote_data.get('bid_price', 0))
            change = 0
            change_percent = 0
            prev_close = current_price
        
        return {
            "symbol": symbol.upper(),
            "price": current_price,
            "change": change,
            "changePercent": change_percent,
            "volume": quote_data.get('ask_size', 0) + quote_data.get('bid_size', 0),
            "high": current_price,  # Would need intraday data for actual high
            "low": current_price,   # Would need intraday data for actual low
            "open": prev_close,
            "previousClose": prev_close,
            "bid": quote_data.get('bid_price', 0),
            "ask": quote_data.get('ask_price', 0),
            "bid_size": quote_data.get('bid_size', 0),
            "ask_size": quote_data.get('ask_size', 0)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))