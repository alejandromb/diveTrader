"""
Type-Safe Strategy API using SQLModel
Auto-generated schemas, validation, and TypeScript types
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List, Dict, Any, Optional
from database.sqlmodel_database import get_session
from database.sqlmodel_models import (
    Strategy, BTCScalpingSettings, PortfolioDistributorSettings,
    StrategyTypeEnum, InvestmentFrequencyEnum
)
from services.typed_strategy_runner import typed_strategy_runner
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v2/strategies", tags=["typed-strategies"])

# Response Models (avoid inheritance issues with relationships)
from pydantic import BaseModel
from datetime import datetime

class StrategyResponse(BaseModel):
    """Strategy response model"""
    id: int
    name: str
    strategy_type: StrategyTypeEnum
    is_active: bool
    initial_capital: float
    current_capital: float
    created_at: datetime
    updated_at: datetime
    config: Optional[str] = None
    is_running: Optional[bool] = False

class BTCSettingsResponse(BaseModel):
    """BTC Settings response model"""
    strategy_id: int
    check_interval: int
    position_size: float
    take_profit_pct: float
    stop_loss_pct: float
    short_ma_periods: int 
    long_ma_periods: int
    rsi_oversold: int
    rsi_overbought: int
    max_positions: int
    min_volume: int
    use_ai_analysis: bool
    ai_confidence_threshold: float
    combine_ai_with_technical: bool
    paper_trading_mode: bool
    fallback_volume: int
    created_at: datetime
    updated_at: datetime

class PortfolioSettingsResponse(BaseModel):
    """Portfolio Settings response model"""
    strategy_id: int
    check_interval: int
    investment_amount: float
    investment_frequency: InvestmentFrequencyEnum
    symbols: str
    allocation_weights: str
    rebalance_threshold: float
    max_position_size: float
    min_cash_reserve: float
    created_at: datetime
    updated_at: datetime
    
    # Computed fields
    symbols_list: Optional[List[str]] = None
    weights_dict: Optional[Dict[str, float]] = None

# Request Models for Updates
class BTCSettingsUpdateRequest(BaseModel):
    """Request model for updating BTC settings"""
    check_interval: Optional[int] = None
    position_size: Optional[float] = None
    take_profit_pct: Optional[float] = None
    stop_loss_pct: Optional[float] = None
    short_ma_periods: Optional[int] = None
    long_ma_periods: Optional[int] = None
    rsi_oversold: Optional[int] = None
    rsi_overbought: Optional[int] = None
    max_positions: Optional[int] = None
    min_volume: Optional[int] = None
    use_ai_analysis: Optional[bool] = None
    ai_confidence_threshold: Optional[float] = None
    combine_ai_with_technical: Optional[bool] = None
    paper_trading_mode: Optional[bool] = None
    fallback_volume: Optional[int] = None

class PortfolioSettingsUpdateRequest(BaseModel):
    """Request model for updating portfolio settings"""
    check_interval: Optional[int] = None
    investment_amount: Optional[float] = None
    investment_frequency: Optional[InvestmentFrequencyEnum] = None
    symbols: Optional[str] = None
    allocation_weights: Optional[str] = None
    rebalance_threshold: Optional[float] = None
    max_position_size: Optional[float] = None
    min_cash_reserve: Optional[float] = None

# Schema endpoints - using different path to avoid routing conflicts
@router.get("/schema/btc-settings")
async def get_btc_settings_schema():
    """Get JSON schema for BTC settings (for TypeScript generation)"""
    return BTCScalpingSettings.model_json_schema()

@router.get("/schema/portfolio-settings")
async def get_portfolio_settings_schema():
    """Get JSON schema for portfolio settings (for TypeScript generation)"""
    return PortfolioDistributorSettings.model_json_schema()

@router.get("/enums/strategy-types")
async def get_strategy_types():
    """Get available strategy types"""
    return [{"value": item.value, "name": item.name} for item in StrategyTypeEnum]

@router.get("/enums/investment-frequencies")
async def get_investment_frequencies():
    """Get available investment frequencies"""
    return [{"value": item.value, "name": item.name} for item in InvestmentFrequencyEnum]

@router.get("/", response_model=List[StrategyResponse])
async def get_all_strategies(session: Session = Depends(get_session)):
    """Get all strategies with running status"""
    try:
        statement = select(Strategy)
        strategies = session.exec(statement).all()
        
        # Add running status to each strategy
        strategies_with_status = []
        for strategy in strategies:
            strategy_response = StrategyResponse(
                id=strategy.id,
                name=strategy.name,
                strategy_type=strategy.strategy_type,
                is_active=strategy.is_active,
                initial_capital=strategy.initial_capital,
                current_capital=strategy.current_capital,
                created_at=strategy.created_at,
                updated_at=strategy.updated_at,
                config=strategy.config,
                is_running=typed_strategy_runner.is_strategy_running(strategy.id)
            )
            strategies_with_status.append(strategy_response)
        
        return strategies_with_status
        
    except Exception as e:
        logger.error(f"Error getting strategies: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get strategies"
        )

@router.get("/{strategy_id}", response_model=StrategyResponse)
async def get_strategy(strategy_id: int, session: Session = Depends(get_session)):
    """Get a specific strategy"""
    try:
        strategy = session.get(Strategy, strategy_id)
        if not strategy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Strategy {strategy_id} not found"
            )
        
        strategy_dict = strategy.model_dump()
        strategy_dict['is_running'] = typed_strategy_runner.is_strategy_running(strategy_id)
        
        return StrategyResponse(**strategy_dict)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting strategy {strategy_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get strategy"
        )

@router.post("/{strategy_id}/start")
async def start_strategy(strategy_id: int, session: Session = Depends(get_session)):
    """Start a strategy"""
    try:
        # Verify strategy exists
        strategy = session.get(Strategy, strategy_id)
        if not strategy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Strategy {strategy_id} not found"
            )
        
        # Start the strategy
        success = typed_strategy_runner.start_strategy(strategy_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to start strategy"
            )
        
        return {"message": f"Strategy {strategy_id} started successfully", "is_running": True}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting strategy {strategy_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start strategy"
        )

@router.post("/{strategy_id}/stop")
async def stop_strategy(strategy_id: int, session: Session = Depends(get_session)):
    """Stop a strategy"""
    try:
        # Verify strategy exists
        strategy = session.get(Strategy, strategy_id)
        if not strategy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Strategy {strategy_id} not found"
            )
        
        # Stop the strategy
        success = typed_strategy_runner.stop_strategy(strategy_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to stop strategy"
            )
        
        return {"message": f"Strategy {strategy_id} stopped successfully", "is_running": False}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error stopping strategy {strategy_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to stop strategy"
        )

@router.get("/{strategy_id}/status")
async def get_strategy_status(strategy_id: int, session: Session = Depends(get_session)):
    """Get detailed strategy status"""
    try:
        # Verify strategy exists
        strategy = session.get(Strategy, strategy_id)
        if not strategy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Strategy {strategy_id} not found"
            )
        
        # Get detailed status from strategy runner
        status = typed_strategy_runner.get_strategy_status(strategy_id)
        
        return status
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting strategy status {strategy_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get strategy status"
        )

# BTC Scalping Settings Endpoints
@router.get("/{strategy_id}/btc-settings", response_model=BTCSettingsResponse)
async def get_btc_settings(strategy_id: int, session: Session = Depends(get_session)):
    """Get BTC scalping settings for a strategy"""
    try:
        # Verify strategy exists and is BTC type
        strategy = session.get(Strategy, strategy_id)
        if not strategy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Strategy {strategy_id} not found"
            )
        
        if strategy.strategy_type != StrategyTypeEnum.BTC_SCALPING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Strategy {strategy_id} is not a BTC scalping strategy"
            )
        
        # Get settings
        settings = session.get(BTCScalpingSettings, strategy_id)
        if not settings:
            # Create default settings
            settings = BTCScalpingSettings(strategy_id=strategy_id)
            session.add(settings)
            session.commit()
            session.refresh(settings)
        
        return settings
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting BTC settings for strategy {strategy_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get BTC settings"
        )

@router.put("/{strategy_id}/btc-settings", response_model=BTCSettingsResponse)
async def update_btc_settings(
    strategy_id: int, 
    settings_update: BTCSettingsUpdateRequest,
    session: Session = Depends(get_session)
):
    """Update BTC scalping settings"""
    try:
        # Verify strategy exists and is BTC type
        strategy = session.get(Strategy, strategy_id)
        if not strategy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Strategy {strategy_id} not found"
            )
        
        if strategy.strategy_type != StrategyTypeEnum.BTC_SCALPING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Strategy {strategy_id} is not a BTC scalping strategy"
            )
        
        # Get existing settings or create new ones
        settings = session.get(BTCScalpingSettings, strategy_id)
        if not settings:
            settings = BTCScalpingSettings(strategy_id=strategy_id)
        
        # Update fields (SQLModel will validate automatically)
        update_data = settings_update.model_dump(exclude_unset=True, exclude={'strategy_id', 'created_at', 'updated_at'})
        for field, value in update_data.items():
            setattr(settings, field, value)
        
        # Update timestamp
        from datetime import datetime
        settings.updated_at = datetime.utcnow()
        
        session.add(settings)
        session.commit()
        session.refresh(settings)
        
        logger.info(f"Updated BTC settings for strategy {strategy_id}")
        
        # Convert SQLModel to response model
        return BTCSettingsResponse(
            strategy_id=settings.strategy_id,
            check_interval=settings.check_interval,
            position_size=settings.position_size,
            take_profit_pct=settings.take_profit_pct,
            stop_loss_pct=settings.stop_loss_pct,
            short_ma_periods=settings.short_ma_periods,
            long_ma_periods=settings.long_ma_periods,
            rsi_oversold=settings.rsi_oversold,
            rsi_overbought=settings.rsi_overbought,
            max_positions=settings.max_positions,
            min_volume=settings.min_volume,
            use_ai_analysis=settings.use_ai_analysis,
            ai_confidence_threshold=settings.ai_confidence_threshold,
            combine_ai_with_technical=settings.combine_ai_with_technical,
            paper_trading_mode=settings.paper_trading_mode,
            fallback_volume=settings.fallback_volume,
            created_at=settings.created_at,
            updated_at=settings.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating BTC settings for strategy {strategy_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update BTC settings"
        )

# Portfolio Settings Endpoints
@router.get("/{strategy_id}/portfolio-settings", response_model=PortfolioSettingsResponse)
async def get_portfolio_settings(strategy_id: int, session: Session = Depends(get_session)):
    """Get portfolio distributor settings for a strategy"""
    try:
        # Verify strategy exists and is portfolio type
        strategy = session.get(Strategy, strategy_id)
        if not strategy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Strategy {strategy_id} not found"
            )
        
        if strategy.strategy_type != StrategyTypeEnum.PORTFOLIO_DISTRIBUTOR:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Strategy {strategy_id} is not a portfolio distributor strategy"
            )
        
        # Get settings
        settings = session.get(PortfolioDistributorSettings, strategy_id)
        if not settings:
            # Create default settings
            settings = PortfolioDistributorSettings(strategy_id=strategy_id)
            session.add(settings)
            session.commit()
            session.refresh(settings)
        
        # Convert SQLModel to response model
        return PortfolioSettingsResponse(
            strategy_id=settings.strategy_id,
            check_interval=settings.check_interval,
            investment_amount=settings.investment_amount,
            investment_frequency=settings.investment_frequency,
            symbols=settings.symbols,
            allocation_weights=settings.allocation_weights,
            rebalance_threshold=settings.rebalance_threshold,
            max_position_size=settings.max_position_size,
            min_cash_reserve=settings.min_cash_reserve,
            created_at=settings.created_at,
            updated_at=settings.updated_at,
            symbols_list=settings.symbols_list,
            weights_dict=settings.weights_dict
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting portfolio settings for strategy {strategy_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get portfolio settings"
        )

@router.put("/{strategy_id}/portfolio-settings", response_model=PortfolioSettingsResponse)
async def update_portfolio_settings(
    strategy_id: int,
    settings_update: PortfolioSettingsUpdateRequest,
    session: Session = Depends(get_session)
):
    """Update portfolio distributor settings"""
    try:
        # Verify strategy exists and is portfolio type
        strategy = session.get(Strategy, strategy_id)
        if not strategy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Strategy {strategy_id} not found"
            )
        
        if strategy.strategy_type != StrategyTypeEnum.PORTFOLIO_DISTRIBUTOR:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Strategy {strategy_id} is not a portfolio distributor strategy"
            )
        
        # Get existing settings or create new ones
        settings = session.get(PortfolioDistributorSettings, strategy_id)
        if not settings:
            settings = PortfolioDistributorSettings(strategy_id=strategy_id)
        
        # Update fields (SQLModel will validate automatically)
        update_data = settings_update.model_dump(exclude_unset=True, exclude={'strategy_id', 'created_at', 'updated_at'})
        for field, value in update_data.items():
            setattr(settings, field, value)
        
        # Update timestamp
        from datetime import datetime
        settings.updated_at = datetime.utcnow()
        
        session.add(settings)
        session.commit()
        session.refresh(settings)
        
        logger.info(f"Updated portfolio settings for strategy {strategy_id}")
        
        # Convert SQLModel to response model
        return PortfolioSettingsResponse(
            strategy_id=settings.strategy_id,
            check_interval=settings.check_interval,
            investment_amount=settings.investment_amount,
            investment_frequency=settings.investment_frequency,
            symbols=settings.symbols,
            allocation_weights=settings.allocation_weights,
            rebalance_threshold=settings.rebalance_threshold,
            max_position_size=settings.max_position_size,
            min_cash_reserve=settings.min_cash_reserve,
            created_at=settings.created_at,
            updated_at=settings.updated_at,
            symbols_list=settings.symbols_list,
            weights_dict=settings.weights_dict
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating portfolio settings for strategy {strategy_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update portfolio settings"
        )

# Schema and enum endpoints moved to top of file to avoid route conflicts