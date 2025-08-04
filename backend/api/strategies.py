from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.database import get_db
from database.models import Strategy, StrategyType
from services.performance_service import PerformanceService
from services.trading_service import TradingService
from services.strategy_runner import strategy_runner
from services.backtesting_service import BacktestingService
from pydantic import BaseModel
from typing import List, Optional
import json

router = APIRouter(prefix="/api/strategies", tags=["strategies"])
performance_service = PerformanceService()
trading_service = TradingService()
backtesting_service = BacktestingService()

class StrategyCreate(BaseModel):
    name: str
    strategy_type: StrategyType
    initial_capital: float
    config: Optional[dict] = {}

class StrategyResponse(BaseModel):
    id: int
    name: str
    strategy_type: StrategyType
    is_active: bool
    initial_capital: float
    current_capital: float
    created_at: str

@router.get("/", response_model=List[StrategyResponse])
async def get_strategies(db: Session = Depends(get_db)):
    """Get all trading strategies"""
    strategies = db.query(Strategy).all()
    return [
        StrategyResponse(
            id=s.id,
            name=s.name,
            strategy_type=s.strategy_type,
            is_active=s.is_active,
            initial_capital=s.initial_capital,
            current_capital=s.current_capital,
            created_at=s.created_at.isoformat()
        )
        for s in strategies
    ]

@router.post("/", response_model=StrategyResponse)
async def create_strategy(strategy: StrategyCreate, db: Session = Depends(get_db)):
    """Create a new trading strategy"""
    db_strategy = Strategy(
        name=strategy.name,
        strategy_type=strategy.strategy_type,
        initial_capital=strategy.initial_capital,
        current_capital=strategy.initial_capital,
        config=json.dumps(strategy.config)
    )
    
    db.add(db_strategy)
    db.commit()
    db.refresh(db_strategy)
    
    return StrategyResponse(
        id=db_strategy.id,
        name=db_strategy.name,
        strategy_type=db_strategy.strategy_type,
        is_active=db_strategy.is_active,
        initial_capital=db_strategy.initial_capital,
        current_capital=db_strategy.current_capital,
        created_at=db_strategy.created_at.isoformat()
    )

@router.get("/{strategy_id}/performance")
async def get_strategy_performance(strategy_id: int, db: Session = Depends(get_db)):
    """Get comprehensive performance metrics for a strategy"""
    try:
        performance = performance_service.calculate_strategy_performance(strategy_id, db)
        risk_metrics = performance_service.calculate_risk_metrics(strategy_id, db)
        
        return {
            **performance,
            **risk_metrics
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/{strategy_id}/daily-metrics")
async def get_daily_metrics(strategy_id: int, days: int = 30, db: Session = Depends(get_db)):
    """Get daily performance metrics for charting"""
    try:
        return performance_service.calculate_daily_metrics(strategy_id, db, days)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/{strategy_id}/portfolio")
async def get_portfolio_breakdown(strategy_id: int, db: Session = Depends(get_db)):
    """Get current portfolio breakdown by symbol"""
    try:
        return performance_service.get_portfolio_breakdown(strategy_id, db)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/{strategy_id}/start")
async def start_strategy(strategy_id: int, db: Session = Depends(get_db)):
    """Start a trading strategy"""
    strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    
    # Check if already running
    if strategy_runner.is_strategy_running(strategy_id):
        return {"message": f"Strategy {strategy.name} is already running"}
    
    # Activate in database
    strategy.is_active = True
    db.commit()
    
    # Start strategy runner
    success = strategy_runner.start_strategy(strategy_id)
    if success:
        return {"message": f"Strategy {strategy.name} started successfully"}
    else:
        # Revert database change if runner failed
        strategy.is_active = False
        db.commit()
        raise HTTPException(status_code=500, detail="Failed to start strategy")

@router.post("/{strategy_id}/stop")
async def stop_strategy(strategy_id: int, db: Session = Depends(get_db)):
    """Stop a trading strategy"""
    strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    
    # Deactivate in database
    strategy.is_active = False
    db.commit()
    
    # Stop strategy runner
    success = strategy_runner.stop_strategy(strategy_id)
    
    status = "stopped successfully" if success else "stopped (may have already been stopped)"
    return {"message": f"Strategy {strategy.name} {status}"}

@router.get("/{strategy_id}/status")
async def get_strategy_status(strategy_id: int, db: Session = Depends(get_db)):
    """Get strategy runtime status"""
    strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
        
    is_running = strategy_runner.is_strategy_running(strategy_id)
    strategy_instance = strategy_runner.strategy_instances.get(strategy_id)
    
    status = {
        "strategy_id": strategy_id,
        "name": strategy.name,
        "is_active": strategy.is_active,
        "is_running": is_running,
        "strategy_type": strategy.strategy_type.value
    }
    
    # Add detailed status if strategy instance exists
    if strategy_instance and hasattr(strategy_instance, 'get_status'):
        status.update(strategy_instance.get_status())
        
    return status

@router.get("/running")
async def get_running_strategies():
    """Get list of currently running strategies"""
    running_ids = strategy_runner.get_running_strategies()
    return {"running_strategy_ids": running_ids, "count": len(running_ids)}

class BacktestRequest(BaseModel):
    days_back: int = 30
    initial_capital: float = 10000.0
    config: Optional[dict] = {}

@router.post("/{strategy_id}/backtest")
async def run_backtest(strategy_id: int, request: BacktestRequest, db: Session = Depends(get_db)):
    """Run backtest for a strategy"""
    strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
        
    if strategy.strategy_type != StrategyType.BTC_SCALPING:
        raise HTTPException(status_code=400, detail="Backtesting only available for BTC scalping strategy")
        
    try:
        results = backtesting_service.run_backtest(
            strategy_config=request.config,
            symbol="BTC/USD",
            days_back=request.days_back,
            initial_capital=request.initial_capital
        )
        
        return results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Backtest failed: {str(e)}")

@router.post("/{strategy_id}/sync-positions")
async def sync_positions(strategy_id: int, db: Session = Depends(get_db)):
    """Sync positions from Alpaca to database"""
    try:
        trading_service.update_positions(strategy_id, db)
        trading_service.update_filled_orders(strategy_id, db)
        performance_service.update_daily_performance(strategy_id, db)
        
        return {"message": "Positions synced successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))