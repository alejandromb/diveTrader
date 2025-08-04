import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from database.models import StrategyEventLog, EventLogLevel

logger = logging.getLogger(__name__)

class StrategyEventLogger:
    """Service for logging strategy events and activities"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def log_event(self, db: Session, strategy_id: int, level: EventLogLevel, 
                  event_type: str, message: str, details: Dict[str, Any] = None):
        """Log a strategy event to the database"""
        try:
            event_log = StrategyEventLog(
                strategy_id=strategy_id,
                level=level,
                event_type=event_type,
                message=message,
                details=json.dumps(details) if details else None,
                timestamp=datetime.utcnow()
            )
            
            db.add(event_log)
            db.commit()
            
            # Also log to application logger
            log_level = {
                EventLogLevel.DEBUG: logging.DEBUG,
                EventLogLevel.INFO: logging.INFO,
                EventLogLevel.WARN: logging.WARNING,
                EventLogLevel.ERROR: logging.ERROR,
                EventLogLevel.CRITICAL: logging.CRITICAL
            }.get(level, logging.INFO)
            
            self.logger.log(log_level, f"Strategy {strategy_id} - {event_type}: {message}")
            
        except Exception as e:
            self.logger.error(f"Failed to log strategy event: {e}")
    
    def log_debug(self, db: Session, strategy_id: int, event_type: str, message: str, details: Dict = None):
        """Log a debug event"""
        self.log_event(db, strategy_id, EventLogLevel.DEBUG, event_type, message, details)
    
    def log_info(self, db: Session, strategy_id: int, event_type: str, message: str, details: Dict = None):
        """Log an info event"""
        self.log_event(db, strategy_id, EventLogLevel.INFO, event_type, message, details)
    
    def log_warning(self, db: Session, strategy_id: int, event_type: str, message: str, details: Dict = None):
        """Log a warning event"""
        self.log_event(db, strategy_id, EventLogLevel.WARN, event_type, message, details)
    
    def log_error(self, db: Session, strategy_id: int, event_type: str, message: str, details: Dict = None):
        """Log an error event"""
        self.log_event(db, strategy_id, EventLogLevel.ERROR, event_type, message, details)
    
    def log_critical(self, db: Session, strategy_id: int, event_type: str, message: str, details: Dict = None):
        """Log a critical event"""
        self.log_event(db, strategy_id, EventLogLevel.CRITICAL, event_type, message, details)
    
    def log_strategy_start(self, db: Session, strategy_id: int):
        """Log strategy start event"""
        self.log_info(db, strategy_id, "strategy_lifecycle", "Strategy started")
    
    def log_strategy_stop(self, db: Session, strategy_id: int):
        """Log strategy stop event"""
        self.log_info(db, strategy_id, "strategy_lifecycle", "Strategy stopped")
    
    def log_trade_check(self, db: Session, strategy_id: int, symbol: str, signal: Optional[str] = None, details: Dict = None):
        """Log a trade signal check"""
        message = f"Checked trading signals for {symbol}"
        if signal:
            message += f" - Signal: {signal}"
        
        log_details = {"symbol": symbol}
        if signal:
            log_details["signal"] = signal
        if details:
            log_details.update(details)
            
        self.log_info(db, strategy_id, "trade_check", message, log_details)
    
    def log_signal_generated(self, db: Session, strategy_id: int, symbol: str, signal: str, 
                           confidence: float = None, details: Dict = None):
        """Log a trading signal generation"""
        message = f"Generated {signal} signal for {symbol}"
        if confidence:
            message += f" (confidence: {confidence:.2f})"
        
        log_details = {"symbol": symbol, "signal": signal}
        if confidence:
            log_details["confidence"] = confidence
        if details:
            log_details.update(details)
            
        self.log_info(db, strategy_id, "signal_generated", message, log_details)
    
    def log_order_placed(self, db: Session, strategy_id: int, symbol: str, side: str, 
                        quantity: float, price: float = None, order_id: str = None):
        """Log an order placement"""
        message = f"Placed {side} order for {quantity} shares of {symbol}"
        if price:
            message += f" at ${price:.2f}"
        
        details = {
            "symbol": symbol,
            "side": side,
            "quantity": quantity
        }
        if price:
            details["price"] = price
        if order_id:
            details["order_id"] = order_id
            
        self.log_info(db, strategy_id, "order_placed", message, details)
    
    def log_order_filled(self, db: Session, strategy_id: int, symbol: str, side: str, 
                        quantity: float, price: float, order_id: str = None):
        """Log an order fill"""
        message = f"Filled {side} order: {quantity} shares of {symbol} at ${price:.2f}"
        
        details = {
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "price": price
        }
        if order_id:
            details["order_id"] = order_id
            
        self.log_info(db, strategy_id, "order_filled", message, details)
    
    def log_risk_alert(self, db: Session, strategy_id: int, alert_type: str, severity: str, message: str):
        """Log a risk management alert"""
        event_level = {
            "low": EventLogLevel.INFO,
            "medium": EventLogLevel.WARN,
            "high": EventLogLevel.ERROR,
            "critical": EventLogLevel.CRITICAL
        }.get(severity, EventLogLevel.WARN)
        
        details = {
            "alert_type": alert_type,
            "severity": severity
        }
        
        self.log_event(db, strategy_id, event_level, "risk_alert", message, details)
    
    def log_performance_update(self, db: Session, strategy_id: int, metrics: Dict):
        """Log performance metrics update"""
        message = f"Performance updated - ROI: {metrics.get('roi', 0):.2f}%, P&L: ${metrics.get('pnl', 0):.2f}"
        self.log_debug(db, strategy_id, "performance_update", message, metrics)
    
    def log_market_data_fetch(self, db: Session, strategy_id: int, symbols: list, success: bool = True, error: str = None):
        """Log market data fetch attempt"""
        if success:
            message = f"Successfully fetched market data for {', '.join(symbols)}"
            self.log_debug(db, strategy_id, "market_data", message, {"symbols": symbols})
        else:
            message = f"Failed to fetch market data for {', '.join(symbols)}"
            if error:
                message += f": {error}"
            self.log_error(db, strategy_id, "market_data", message, {"symbols": symbols, "error": error})
    
    def log_portfolio_rebalance(self, db: Session, strategy_id: int, changes: Dict):
        """Log portfolio rebalancing activity"""
        message = f"Portfolio rebalanced with {len(changes)} changes"
        self.log_info(db, strategy_id, "portfolio_rebalance", message, changes)
    
    def get_recent_events(self, db: Session, strategy_id: int, limit: int = 100, 
                         event_type: str = None, level: EventLogLevel = None):
        """Get recent events for a strategy"""
        try:
            query = db.query(StrategyEventLog).filter(StrategyEventLog.strategy_id == strategy_id)
            
            if event_type:
                query = query.filter(StrategyEventLog.event_type == event_type)
            
            if level:
                query = query.filter(StrategyEventLog.level == level)
            
            events = query.order_by(StrategyEventLog.timestamp.desc()).limit(limit).all()
            
            return [
                {
                    "id": event.id,
                    "level": event.level.value,
                    "event_type": event.event_type,
                    "message": event.message,
                    "details": json.loads(event.details) if event.details else None,
                    "timestamp": event.timestamp.isoformat()
                }
                for event in events
            ]
            
        except Exception as e:
            self.logger.error(f"Error fetching strategy events: {e}")
            return []

# Global instance
strategy_event_logger = StrategyEventLogger()