from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, List
from database.database import get_db
from services.risk_management_service import RiskManagementService
from services.trading_service import TradingService
from pydantic import BaseModel

router = APIRouter(prefix="/api/risk", tags=["risk-management"])

class RiskLimitsUpdate(BaseModel):
    max_portfolio_risk: float = None
    max_daily_loss: float = None
    max_drawdown: float = None
    max_position_size: float = None
    max_correlation_exposure: float = None
    min_cash_reserve: float = None
    max_leverage: float = None
    stop_loss_required: bool = None
    position_concentration_limit: int = None

class TradeValidationRequest(BaseModel):
    strategy_id: int
    symbol: str
    side: str  # "buy" or "sell"
    quantity: int
    price: float

def get_risk_service(db: Session = Depends(get_db)) -> RiskManagementService:
    trading_service = TradingService()
    return RiskManagementService(trading_service)

@router.get("/summary/{strategy_id}")
async def get_risk_summary(
    strategy_id: int,
    db: Session = Depends(get_db),
    risk_service: RiskManagementService = Depends(get_risk_service)
):
    """Get comprehensive risk summary for a strategy"""
    try:
        summary = risk_service.get_risk_summary(strategy_id, db)
        if "error" in summary:
            raise HTTPException(status_code=404, detail=summary["error"])
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/limits/{strategy_id}")
async def get_risk_limits(
    strategy_id: int,
    db: Session = Depends(get_db),
    risk_service: RiskManagementService = Depends(get_risk_service)
):
    """Get risk limits for a strategy"""
    try:
        limits = risk_service.get_strategy_risk_limits(strategy_id, db)
        return {"strategy_id": strategy_id, "limits": limits}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/limits/{strategy_id}")
async def update_risk_limits(
    strategy_id: int,
    limits: RiskLimitsUpdate,
    db: Session = Depends(get_db)
):
    """Update risk limits for a strategy"""
    try:
        from database.models import Strategy
        import json
        
        strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
        if not strategy:
            raise HTTPException(status_code=404, detail="Strategy not found")
        
        # Parse existing config
        config = json.loads(strategy.config or '{}')
        risk_config = config.get('risk_management', {})
        
        # Update with new limits (only non-None values)
        update_data = limits.dict(exclude_unset=True)
        risk_config.update(update_data)
        
        # Save back to strategy
        config['risk_management'] = risk_config
        strategy.config = json.dumps(config)
        
        db.commit()
        db.refresh(strategy)
        
        return {"message": "Risk limits updated successfully", "limits": risk_config}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/validate-trade")
async def validate_trade(
    request: TradeValidationRequest,
    db: Session = Depends(get_db),
    risk_service: RiskManagementService = Depends(get_risk_service)
):
    """Validate if a trade is allowed based on risk rules"""
    try:
        from alpaca.trading.enums import OrderSide
        
        # Convert string to OrderSide enum
        side = OrderSide.BUY if request.side.lower() == "buy" else OrderSide.SELL
        
        is_valid, alerts = risk_service.validate_trade(
            request.strategy_id,
            request.symbol,
            side,
            request.quantity,
            request.price,
            db
        )
        
        return {
            "is_valid": is_valid,
            "alerts": [
                {
                    "type": alert.alert_type,
                    "severity": alert.severity,
                    "message": alert.message,
                    "timestamp": alert.timestamp.isoformat(),
                    "data": alert.data
                }
                for alert in alerts
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/position-size/{strategy_id}")
async def calculate_position_size(
    strategy_id: int,
    symbol: str,
    entry_price: float,
    stop_loss_price: float = 0,
    db: Session = Depends(get_db),
    risk_service: RiskManagementService = Depends(get_risk_service)
):
    """Calculate recommended position size"""
    try:
        position_size, alerts = risk_service.calculate_position_size(
            strategy_id, symbol, entry_price, stop_loss_price, db
        )
        
        return {
            "strategy_id": strategy_id,
            "symbol": symbol,
            "recommended_size": position_size,
            "entry_price": entry_price,
            "stop_loss_price": stop_loss_price,
            "alerts": [
                {
                    "type": alert.alert_type,
                    "severity": alert.severity,
                    "message": alert.message,
                    "data": alert.data
                }
                for alert in alerts
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/alerts/{strategy_id}")
async def get_risk_alerts(
    strategy_id: int,
    db: Session = Depends(get_db),
    risk_service: RiskManagementService = Depends(get_risk_service)
):
    """Get all current risk alerts for a strategy"""
    try:
        alerts = risk_service.check_strategy_halt_conditions(strategy_id, db)
        
        return {
            "strategy_id": strategy_id,
            "alerts": [
                {
                    "type": alert.alert_type,
                    "severity": alert.severity,
                    "message": alert.message,
                    "timestamp": alert.timestamp.isoformat(),
                    "data": alert.data
                }
                for alert in alerts
            ],
            "status": "critical" if any(a.severity == "critical" for a in alerts) else 
                     "warning" if any(a.severity in ["high", "medium"] for a in alerts) else "healthy"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health-check")
async def risk_health_check():
    """Health check endpoint for risk management service"""
    return {"status": "healthy", "service": "risk_management"}