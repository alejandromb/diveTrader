from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from database.database import get_db
from database.models import EventLogLevel
from services.strategy_event_logger import strategy_event_logger
from pydantic import BaseModel

router = APIRouter(prefix="/api/strategy-events", tags=["strategy-events"])

class EventLogResponse(BaseModel):
    id: int
    level: str
    event_type: str
    message: str
    details: dict = None
    timestamp: str

@router.get("/strategy/{strategy_id}", response_model=List[EventLogResponse])
async def get_strategy_events(
    strategy_id: int,
    db: Session = Depends(get_db),
    limit: int = Query(100, description="Maximum number of events to return"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    level: Optional[str] = Query(None, description="Filter by log level")
):
    """Get event logs for a specific strategy"""
    try:
        # Convert string level to enum if provided
        level_enum = None
        if level:
            try:
                level_enum = EventLogLevel(level.lower())
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid log level: {level}")
        
        events = strategy_event_logger.get_recent_events(
            db, strategy_id, limit, event_type, level_enum
        )
        
        return events
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/strategy/{strategy_id}/latest")
async def get_latest_event(
    strategy_id: int,
    db: Session = Depends(get_db)
):
    """Get the most recent event for a strategy"""
    try:
        events = strategy_event_logger.get_recent_events(db, strategy_id, limit=1)
        if events:
            return events[0]
        return None
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/strategy/{strategy_id}/summary")
async def get_events_summary(
    strategy_id: int,
    db: Session = Depends(get_db)
):
    """Get a summary of recent events for a strategy"""
    try:
        # Get recent events by type
        recent_events = strategy_event_logger.get_recent_events(db, strategy_id, limit=50)
        
        # Count events by type and level
        event_counts = {}
        level_counts = {"debug": 0, "info": 0, "warn": 0, "error": 0, "critical": 0}
        
        for event in recent_events:
            event_type = event["event_type"]
            level = event["level"]
            
            event_counts[event_type] = event_counts.get(event_type, 0) + 1
            level_counts[level] = level_counts.get(level, 0) + 1
        
        # Get latest event of each important type
        latest_events = {}
        important_types = ["trade_check", "signal_generated", "order_placed", "risk_alert", "strategy_lifecycle"]
        
        for event in recent_events:
            event_type = event["event_type"]
            if event_type in important_types and event_type not in latest_events:
                latest_events[event_type] = event
        
        return {
            "strategy_id": strategy_id,
            "total_events": len(recent_events),
            "event_counts": event_counts,
            "level_counts": level_counts,
            "latest_events": latest_events,
            "last_activity": recent_events[0]["timestamp"] if recent_events else None
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/strategy/{strategy_id}")
async def clear_strategy_events(
    strategy_id: int,
    db: Session = Depends(get_db),
    keep_recent: int = Query(10, description="Number of recent events to keep")
):
    """Clear old events for a strategy, keeping only the most recent ones"""
    try:
        from database.models import StrategyEventLog
        
        # Get events to keep
        recent_events = db.query(StrategyEventLog).filter(
            StrategyEventLog.strategy_id == strategy_id
        ).order_by(StrategyEventLog.timestamp.desc()).limit(keep_recent).all()
        
        if recent_events:
            # Get the timestamp of the oldest event to keep
            oldest_keep_timestamp = recent_events[-1].timestamp
            
            # Delete older events
            deleted_count = db.query(StrategyEventLog).filter(
                StrategyEventLog.strategy_id == strategy_id,
                StrategyEventLog.timestamp < oldest_keep_timestamp
            ).delete()
        else:
            # No recent events, delete all
            deleted_count = db.query(StrategyEventLog).filter(
                StrategyEventLog.strategy_id == strategy_id
            ).delete()
        
        db.commit()
        
        return {
            "message": f"Cleared {deleted_count} old events",
            "deleted_count": deleted_count,
            "kept_recent": keep_recent
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/event-types")
async def get_available_event_types(db: Session = Depends(get_db)):
    """Get list of available event types"""
    try:
        from database.models import StrategyEventLog
        from sqlalchemy import distinct
        
        event_types = db.query(distinct(StrategyEventLog.event_type)).all()
        types_list = [row[0] for row in event_types if row[0]]
        
        return {
            "event_types": sorted(types_list),
            "common_types": [
                "strategy_lifecycle",
                "trade_check", 
                "signal_generated",
                "order_placed",
                "order_filled",
                "risk_alert",
                "performance_update",
                "market_data",
                "portfolio_rebalance"
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def events_health_check():
    """Health check for strategy events service"""
    return {"status": "healthy", "service": "strategy_events"}