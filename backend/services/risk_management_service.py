import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func
from database.models import Strategy, Position, Trade, PerformanceMetric
from services.trading_service import TradingService
from alpaca.trading.enums import OrderSide

logger = logging.getLogger(__name__)

class RiskAlert:
    def __init__(self, alert_type: str, severity: str, message: str, strategy_id: int, data: Dict = None):
        self.alert_type = alert_type  # "drawdown", "position_size", "daily_loss", "correlation", etc.
        self.severity = severity      # "low", "medium", "high", "critical"
        self.message = message
        self.strategy_id = strategy_id
        self.timestamp = datetime.utcnow()
        self.data = data or {}

class RiskManagementService:
    def __init__(self, trading_service: TradingService):
        self.trading_service = trading_service
        self.logger = logging.getLogger(__name__)
        
        # Default risk limits
        self.default_limits = {
            "max_portfolio_risk": 25.0,        # Max % of portfolio at risk
            "max_daily_loss": 5.0,             # Max daily loss %
            "max_drawdown": 15.0,              # Max drawdown %
            "max_position_size": 10.0,         # Max single position %
            "max_correlation_exposure": 40.0,  # Max exposure to correlated assets
            "min_cash_reserve": 10.0,          # Min cash reserve %
            "max_leverage": 1.0,               # Max leverage ratio
            "stop_loss_required": True,        # Require stop losses
            "position_concentration_limit": 5  # Max positions in same sector
        }
    
    def get_strategy_risk_limits(self, strategy_id: int, db: Session) -> Dict:
        """Get risk limits for a strategy (custom or default)"""
        try:
            strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
            if not strategy:
                return self.default_limits
            
            config = json.loads(strategy.config or '{}')
            risk_config = config.get('risk_management', {})
            
            # Merge with defaults
            limits = self.default_limits.copy()
            limits.update(risk_config)
            
            return limits
            
        except Exception as e:
            self.logger.error(f"Error getting risk limits: {e}")
            return self.default_limits
    
    def calculate_position_size(self, strategy_id: int, symbol: str, entry_price: float, 
                              stop_loss_price: float, db: Session) -> Tuple[int, List[RiskAlert]]:
        """Calculate safe position size based on risk management rules"""
        alerts = []
        
        try:
            strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
            if not strategy:
                return 0, [RiskAlert("error", "high", "Strategy not found", strategy_id)]
            
            limits = self.get_strategy_risk_limits(strategy_id, db)
            
            # Get strategy config for risk per trade
            config = json.loads(strategy.config or '{}')
            
            if strategy.strategy_type.value == 'btc_scalping':
                risk_per_trade = config.get('btc_scalping', {}).get('risk_per_trade', 2.0)
            else:
                risk_per_trade = limits.get('risk_per_trade', 2.0)
            
            # Calculate risk amount
            risk_amount = strategy.current_capital * (risk_per_trade / 100.0)
            
            # Calculate position size based on stop loss
            if stop_loss_price > 0 and entry_price > 0:
                risk_per_share = abs(entry_price - stop_loss_price)
                if risk_per_share > 0:
                    position_size = int(risk_amount / risk_per_share)
                else:
                    position_size = 0
                    alerts.append(RiskAlert(
                        "position_sizing", "high", 
                        "Invalid stop loss price", strategy_id
                    ))
            else:
                # Fallback: use max position size limit
                max_position_value = strategy.current_capital * (limits['max_position_size'] / 100.0)
                position_size = int(max_position_value / entry_price) if entry_price > 0 else 0
            
            # Apply additional limits
            max_shares_by_capital = int((strategy.current_capital * limits['max_position_size'] / 100.0) / entry_price)
            position_size = min(position_size, max_shares_by_capital)
            
            # Check minimum position
            if position_size < 1:
                alerts.append(RiskAlert(
                    "position_sizing", "medium", 
                    f"Position size too small: {position_size}", strategy_id
                ))
                return 0, alerts
            
            # Validate against current portfolio
            portfolio_value = self.calculate_portfolio_value(strategy_id, db)
            position_value = position_size * entry_price
            position_percentage = (position_value / portfolio_value) * 100 if portfolio_value > 0 else 0
            
            if position_percentage > limits['max_position_size']:
                alerts.append(RiskAlert(
                    "position_size", "high", 
                    f"Position would be {position_percentage:.1f}% of portfolio (max: {limits['max_position_size']}%)", 
                    strategy_id, {"position_percentage": position_percentage}
                ))
                # Reduce position size to comply
                position_size = int((limits['max_position_size'] / 100.0) * portfolio_value / entry_price)
            
            return position_size, alerts
            
        except Exception as e:
            self.logger.error(f"Error calculating position size: {e}")
            return 0, [RiskAlert("error", "critical", f"Position sizing error: {str(e)}", strategy_id)]
    
    def check_drawdown_limits(self, strategy_id: int, db: Session) -> List[RiskAlert]:
        """Check if strategy is approaching drawdown limits"""
        alerts = []
        
        try:
            strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
            if not strategy:
                return alerts
            
            limits = self.get_strategy_risk_limits(strategy_id, db)
            
            # Calculate current drawdown
            peak_capital = self.get_peak_capital(strategy_id, db)
            current_capital = strategy.current_capital
            
            if peak_capital > 0:
                drawdown_percent = ((peak_capital - current_capital) / peak_capital) * 100
                max_drawdown = limits['max_drawdown']
                
                if drawdown_percent >= max_drawdown:
                    alerts.append(RiskAlert(
                        "drawdown", "critical", 
                        f"Maximum drawdown reached: {drawdown_percent:.1f}% (limit: {max_drawdown}%)", 
                        strategy_id, {"drawdown_percent": drawdown_percent, "limit": max_drawdown}
                    ))
                elif drawdown_percent >= max_drawdown * 0.8:  # 80% of limit
                    alerts.append(RiskAlert(
                        "drawdown", "high", 
                        f"Approaching drawdown limit: {drawdown_percent:.1f}% (limit: {max_drawdown}%)", 
                        strategy_id, {"drawdown_percent": drawdown_percent, "limit": max_drawdown}
                    ))
                elif drawdown_percent >= max_drawdown * 0.6:  # 60% of limit
                    alerts.append(RiskAlert(
                        "drawdown", "medium", 
                        f"Drawdown warning: {drawdown_percent:.1f}% (limit: {max_drawdown}%)", 
                        strategy_id, {"drawdown_percent": drawdown_percent, "limit": max_drawdown}
                    ))
            
            return alerts
            
        except Exception as e:
            self.logger.error(f"Error checking drawdown: {e}")
            return [RiskAlert("error", "high", f"Drawdown check error: {str(e)}", strategy_id)]
    
    def check_daily_loss_limits(self, strategy_id: int, db: Session) -> List[RiskAlert]:
        """Check daily loss limits"""
        alerts = []
        
        try:
            limits = self.get_strategy_risk_limits(strategy_id, db)
            
            # Get today's P&L
            today = datetime.utcnow().date()
            today_start = datetime.combine(today, datetime.min.time())
            
            daily_pnl = db.query(Trade).filter(
                Trade.strategy_id == strategy_id,
                Trade.executed_at >= today_start,
                Trade.status == "filled"
            ).with_entities(
                func.sum(Trade.realized_pnl).label('total_pnl')
            ).scalar() or 0.0
            
            strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
            if strategy and daily_pnl < 0:
                loss_percent = abs(daily_pnl / strategy.current_capital) * 100
                max_daily_loss = limits['max_daily_loss']
                
                if loss_percent >= max_daily_loss:
                    alerts.append(RiskAlert(
                        "daily_loss", "critical", 
                        f"Daily loss limit exceeded: {loss_percent:.1f}% (limit: {max_daily_loss}%)", 
                        strategy_id, {"loss_percent": loss_percent, "daily_pnl": daily_pnl}
                    ))
                elif loss_percent >= max_daily_loss * 0.8:
                    alerts.append(RiskAlert(
                        "daily_loss", "high", 
                        f"Approaching daily loss limit: {loss_percent:.1f}% (limit: {max_daily_loss}%)", 
                        strategy_id, {"loss_percent": loss_percent, "daily_pnl": daily_pnl}
                    ))
            
            return alerts
            
        except Exception as e:
            self.logger.error(f"Error checking daily loss: {e}")
            return [RiskAlert("error", "medium", f"Daily loss check error: {str(e)}", strategy_id)]
    
    def check_position_concentration(self, strategy_id: int, db: Session) -> List[RiskAlert]:
        """Check for over-concentration in positions"""
        alerts = []
        
        try:
            limits = self.get_strategy_risk_limits(strategy_id, db)
            positions = db.query(Position).filter(Position.strategy_id == strategy_id).all()
            
            if not positions:
                return alerts
            
            total_value = sum(pos.market_value for pos in positions)
            
            # Check individual position sizes
            for position in positions:
                if total_value > 0:
                    position_percent = (position.market_value / total_value) * 100
                    max_position = limits['max_position_size']
                    
                    if position_percent > max_position:
                        alerts.append(RiskAlert(
                            "concentration", "high", 
                            f"{position.symbol} is {position_percent:.1f}% of portfolio (max: {max_position}%)", 
                            strategy_id, {"symbol": position.symbol, "percentage": position_percent}
                        ))
            
            # Check sector concentration (simplified - based on symbol patterns)
            tech_symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA', 'TSLA']
            tech_exposure = sum(pos.market_value for pos in positions if pos.symbol in tech_symbols)
            
            if total_value > 0:
                tech_percent = (tech_exposure / total_value) * 100
                max_sector = limits.get('max_sector_exposure', 50.0)
                
                if tech_percent > max_sector:
                    alerts.append(RiskAlert(
                        "sector_concentration", "medium", 
                        f"Tech sector exposure: {tech_percent:.1f}% (max: {max_sector}%)", 
                        strategy_id, {"sector": "technology", "percentage": tech_percent}
                    ))
            
            return alerts
            
        except Exception as e:
            self.logger.error(f"Error checking concentration: {e}")
            return [RiskAlert("error", "medium", f"Concentration check error: {str(e)}", strategy_id)]
    
    def validate_trade(self, strategy_id: int, symbol: str, side: OrderSide, 
                      quantity: int, price: float, db: Session) -> Tuple[bool, List[RiskAlert]]:
        """Validate if a trade is allowed based on risk rules"""
        alerts = []
        
        try:
            # Check if strategy should be halted
            halt_alerts = self.check_strategy_halt_conditions(strategy_id, db)
            if any(alert.severity == "critical" for alert in halt_alerts):
                return False, halt_alerts
            
            # Check position sizing
            if side == OrderSide.BUY:
                max_size, size_alerts = self.calculate_position_size(strategy_id, symbol, price, 0, db)
                alerts.extend(size_alerts)
                
                if quantity > max_size:
                    alerts.append(RiskAlert(
                        "position_size", "high", 
                        f"Trade size {quantity} exceeds maximum {max_size}", 
                        strategy_id
                    ))
                    return False, alerts
            
            # Check daily loss limits
            daily_alerts = self.check_daily_loss_limits(strategy_id, db)
            alerts.extend(daily_alerts)
            
            # Block trades if critical daily loss
            if any(alert.alert_type == "daily_loss" and alert.severity == "critical" for alert in daily_alerts):
                return False, alerts
            
            # Check drawdown limits
            drawdown_alerts = self.check_drawdown_limits(strategy_id, db)
            alerts.extend(drawdown_alerts)
            
            # Block trades if critical drawdown
            if any(alert.alert_type == "drawdown" and alert.severity == "critical" for alert in drawdown_alerts):
                return False, alerts
            
            return True, alerts
            
        except Exception as e:
            self.logger.error(f"Error validating trade: {e}")
            return False, [RiskAlert("error", "critical", f"Trade validation error: {str(e)}", strategy_id)]
    
    def check_strategy_halt_conditions(self, strategy_id: int, db: Session) -> List[RiskAlert]:
        """Check if strategy should be automatically halted"""
        alerts = []
        
        # Combine all risk checks
        alerts.extend(self.check_drawdown_limits(strategy_id, db))
        alerts.extend(self.check_daily_loss_limits(strategy_id, db))
        alerts.extend(self.check_position_concentration(strategy_id, db))
        
        return alerts
    
    def get_risk_summary(self, strategy_id: int, db: Session) -> Dict:
        """Get comprehensive risk summary for a strategy"""
        try:
            strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
            if not strategy:
                return {"error": "Strategy not found"}
            
            limits = self.get_strategy_risk_limits(strategy_id, db)
            
            # Calculate current metrics
            peak_capital = self.get_peak_capital(strategy_id, db)
            current_drawdown = 0
            if peak_capital > 0:
                current_drawdown = ((peak_capital - strategy.current_capital) / peak_capital) * 100
            
            # Get daily P&L
            today = datetime.utcnow().date()
            today_start = datetime.combine(today, datetime.min.time())
            daily_pnl = db.query(Trade).filter(
                Trade.strategy_id == strategy_id,
                Trade.executed_at >= today_start,
                Trade.status == "filled"
            ).with_entities(func.sum(Trade.realized_pnl).label('total_pnl')).scalar() or 0.0
            
            daily_loss_percent = 0
            if strategy.current_capital > 0 and daily_pnl < 0:
                daily_loss_percent = abs(daily_pnl / strategy.current_capital) * 100
            
            # Get all current alerts
            all_alerts = self.check_strategy_halt_conditions(strategy_id, db)
            
            return {
                "strategy_id": strategy_id,
                "risk_limits": limits,
                "current_metrics": {
                    "drawdown_percent": current_drawdown,
                    "daily_pnl": daily_pnl,
                    "daily_loss_percent": daily_loss_percent,
                    "portfolio_value": self.calculate_portfolio_value(strategy_id, db)
                },
                "alerts": [
                    {
                        "type": alert.alert_type,
                        "severity": alert.severity,
                        "message": alert.message,
                        "timestamp": alert.timestamp.isoformat(),
                        "data": alert.data
                    }
                    for alert in all_alerts
                ],
                "status": "critical" if any(a.severity == "critical" for a in all_alerts) else 
                         "warning" if any(a.severity in ["high", "medium"] for a in all_alerts) else "healthy"
            }
            
        except Exception as e:
            self.logger.error(f"Error getting risk summary: {e}")
            return {"error": str(e)}
    
    def calculate_portfolio_value(self, strategy_id: int, db: Session) -> float:
        """Calculate total portfolio value"""
        try:
            strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
            if not strategy:
                return 0.0
            
            positions = db.query(Position).filter(Position.strategy_id == strategy_id).all()
            position_value = sum(pos.market_value for pos in positions)
            
            return strategy.current_capital + position_value
            
        except Exception as e:
            self.logger.error(f"Error calculating portfolio value: {e}")
            return 0.0
    
    def get_peak_capital(self, strategy_id: int, db: Session) -> float:
        """Get the peak capital achieved by strategy"""
        try:
            # Get from performance metrics or calculate from trades
            peak = db.query(PerformanceMetric).filter(
                PerformanceMetric.strategy_id == strategy_id
            ).with_entities(
                func.max(PerformanceMetric.total_value).label('peak')
            ).scalar()
            
            if peak:
                return float(peak)
            
            # Fallback: use initial capital as peak
            strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
            return strategy.initial_capital if strategy else 0.0
            
        except Exception as e:
            self.logger.error(f"Error getting peak capital: {e}")
            return 0.0