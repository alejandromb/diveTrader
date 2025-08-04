from sqlalchemy.orm import Session
from database.models import Strategy, Trade, Position, PerformanceMetric
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from typing import List, Dict, Optional

class PerformanceService:
    
    def calculate_strategy_performance(self, strategy_id: int, db: Session) -> Dict:
        """Calculate comprehensive performance metrics for a strategy"""
        strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
        if not strategy:
            raise ValueError("Strategy not found")
        
        trades = db.query(Trade).filter(
            Trade.strategy_id == strategy_id,
            Trade.status == "filled"
        ).order_by(Trade.executed_at).all()
        
        positions = db.query(Position).filter(Position.strategy_id == strategy_id).all()
        
        # Calculate basic metrics
        total_trades = len(trades)
        winning_trades = len([t for t in trades if t.realized_pnl > 0])
        losing_trades = len([t for t in trades if t.realized_pnl < 0])
        
        total_realized_pnl = sum(t.realized_pnl for t in trades)
        total_unrealized_pnl = sum(p.unrealized_pnl for p in positions)
        total_pnl = total_realized_pnl + total_unrealized_pnl
        
        # Calculate position values
        total_position_value = sum(p.market_value for p in positions)
        current_capital = strategy.current_capital
        total_value = current_capital + total_position_value
        
        # ROI calculation
        roi_percentage = ((total_value - strategy.initial_capital) / strategy.initial_capital) * 100
        
        # Win rate
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        return {
            "strategy_id": strategy_id,
            "strategy_name": strategy.name,
            "initial_capital": strategy.initial_capital,
            "current_capital": current_capital,
            "total_position_value": total_position_value,
            "total_value": total_value,
            "total_pnl": total_pnl,
            "roi_percentage": roi_percentage,
            "total_trades": total_trades,
            "winning_trades": winning_trades,
            "losing_trades": losing_trades,
            "win_rate": win_rate,
            "realized_pnl": total_realized_pnl,
            "unrealized_pnl": total_unrealized_pnl
        }
    
    def calculate_daily_metrics(self, strategy_id: int, db: Session, days: int = 30) -> List[Dict]:
        """Calculate daily performance metrics for charting"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get historical performance metrics
        metrics = db.query(PerformanceMetric).filter(
            PerformanceMetric.strategy_id == strategy_id,
            PerformanceMetric.date >= start_date
        ).order_by(PerformanceMetric.date).all()
        
        daily_data = []
        for metric in metrics:
            daily_data.append({
                "date": metric.date.strftime("%Y-%m-%d"),
                "total_value": metric.total_value,
                "daily_pnl": metric.daily_pnl,
                "cumulative_pnl": metric.cumulative_pnl,
                "roi_percentage": metric.roi_percentage
            })
        
        return daily_data
    
    def calculate_risk_metrics(self, strategy_id: int, db: Session) -> Dict:
        """Calculate risk metrics like Sharpe ratio, max drawdown"""
        metrics = db.query(PerformanceMetric).filter(
            PerformanceMetric.strategy_id == strategy_id
        ).order_by(PerformanceMetric.date).all()
        
        if len(metrics) < 2:
            return {
                "sharpe_ratio": None,
                "max_drawdown": None,
                "volatility": None
            }
        
        # Convert to pandas for easier calculation
        df = pd.DataFrame([{
            "date": m.date,
            "total_value": m.total_value,
            "daily_pnl": m.daily_pnl
        } for m in metrics])
        
        # Calculate returns
        df['returns'] = df['daily_pnl'] / df['total_value'].shift(1)
        daily_returns = df['returns'].dropna()
        
        # Sharpe ratio (assuming 0% risk-free rate)
        if len(daily_returns) > 1:
            sharpe_ratio = (daily_returns.mean() / daily_returns.std()) * np.sqrt(252) if daily_returns.std() > 0 else 0
            volatility = daily_returns.std() * np.sqrt(252)
        else:
            sharpe_ratio = 0
            volatility = 0
        
        # Max drawdown
        cumulative_returns = (1 + daily_returns).cumprod()
        peak = cumulative_returns.expanding().max()
        drawdown = (cumulative_returns - peak) / peak
        max_drawdown = drawdown.min() * 100  # Convert to percentage
        
        return {
            "sharpe_ratio": round(sharpe_ratio, 3),
            "max_drawdown": round(max_drawdown, 2),
            "volatility": round(volatility * 100, 2)  # Convert to percentage
        }
    
    def update_daily_performance(self, strategy_id: int, db: Session):
        """Update daily performance metrics (called daily by scheduler)"""
        strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
        if not strategy:
            return
        
        today = datetime.utcnow().date()
        
        # Check if today's metrics already exist
        existing_metric = db.query(PerformanceMetric).filter(
            PerformanceMetric.strategy_id == strategy_id,
            PerformanceMetric.date == today
        ).first()
        
        # Calculate current performance
        performance = self.calculate_strategy_performance(strategy_id, db)
        
        # Get yesterday's metrics for daily P&L calculation
        yesterday = today - timedelta(days=1)
        yesterday_metric = db.query(PerformanceMetric).filter(
            PerformanceMetric.strategy_id == strategy_id,
            PerformanceMetric.date == yesterday
        ).first()
        
        yesterday_value = yesterday_metric.total_value if yesterday_metric else strategy.initial_capital
        daily_pnl = performance["total_value"] - yesterday_value
        
        if existing_metric:
            # Update existing metric
            existing_metric.total_value = performance["total_value"]
            existing_metric.daily_pnl = daily_pnl
            existing_metric.cumulative_pnl = performance["total_pnl"]
            existing_metric.roi_percentage = performance["roi_percentage"]
            existing_metric.total_trades = performance["total_trades"]
            existing_metric.winning_trades = performance["winning_trades"]
            existing_metric.losing_trades = performance["losing_trades"]
            existing_metric.win_rate = performance["win_rate"]
        else:
            # Create new metric
            new_metric = PerformanceMetric(
                strategy_id=strategy_id,
                date=today,
                total_value=performance["total_value"],
                daily_pnl=daily_pnl,
                cumulative_pnl=performance["total_pnl"],
                roi_percentage=performance["roi_percentage"],
                total_trades=performance["total_trades"],
                winning_trades=performance["winning_trades"],
                losing_trades=performance["losing_trades"],
                win_rate=performance["win_rate"]
            )
            db.add(new_metric)
        
        db.commit()
    
    def get_portfolio_breakdown(self, strategy_id: int, db: Session) -> List[Dict]:
        """Get current portfolio breakdown by symbol"""
        positions = db.query(Position).filter(Position.strategy_id == strategy_id).all()
        
        total_value = sum(p.market_value for p in positions)
        
        breakdown = []
        for position in positions:
            percentage = (position.market_value / total_value * 100) if total_value > 0 else 0
            breakdown.append({
                "symbol": position.symbol,
                "quantity": position.quantity,
                "avg_price": position.avg_price,
                "current_price": position.current_price,
                "market_value": position.market_value,
                "unrealized_pnl": position.unrealized_pnl,
                "percentage": round(percentage, 2)
            })
        
        return sorted(breakdown, key=lambda x: x["market_value"], reverse=True)