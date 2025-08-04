from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from database.database import get_db
from database.models import Strategy, StrategySetting, SettingType
from services.strategy_settings_service import strategy_settings_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/strategies", tags=["strategy-settings"])

# Pydantic models for request/response
class SettingRequest(BaseModel):
    key: str
    value: Any
    setting_type: SettingType
    description: Optional[str] = ""
    is_required: Optional[bool] = False

class SettingResponse(BaseModel):
    id: int
    strategy_id: int
    setting_key: str
    setting_value: str
    setting_type: SettingType
    description: Optional[str]
    default_value: Optional[str]
    is_required: bool
    created_at: str
    updated_at: str

class SettingValueResponse(BaseModel):
    key: str
    value: Any
    setting_type: SettingType
    description: Optional[str]

@router.get("/{strategy_id}/settings", response_model=Dict[str, Any])
async def get_strategy_settings(strategy_id: int, db: Session = Depends(get_db)):
    """Get all settings for a strategy"""
    try:
        # Check if strategy exists
        strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
        if not strategy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Strategy {strategy_id} not found"
            )
        
        settings = strategy_settings_service.get_all_settings(db, strategy_id)
        
        # Also get the raw settings with metadata
        raw_settings = db.query(StrategySetting).filter(
            StrategySetting.strategy_id == strategy_id
        ).all()
        
        settings_with_metadata = {}
        for setting in raw_settings:
            parsed_value = strategy_settings_service._parse_setting_value(
                setting.setting_value, setting.setting_type
            )
            settings_with_metadata[setting.setting_key] = {
                "value": parsed_value,
                "type": setting.setting_type.value,
                "description": setting.description,
                "default_value": strategy_settings_service._parse_setting_value(
                    setting.default_value, setting.setting_type
                ) if setting.default_value else None,
                "is_required": setting.is_required,
                "created_at": setting.created_at.isoformat(),
                "updated_at": setting.updated_at.isoformat()
            }
        
        return {
            "strategy_id": strategy_id,
            "strategy_name": strategy.name,
            "strategy_type": strategy.strategy_type.value,
            "settings": settings_with_metadata
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting settings for strategy {strategy_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get strategy settings"
        )

@router.get("/{strategy_id}/settings/{setting_key}")
async def get_strategy_setting(strategy_id: int, setting_key: str, db: Session = Depends(get_db)):
    """Get a specific setting for a strategy"""
    try:
        # Check if strategy exists
        strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
        if not strategy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Strategy {strategy_id} not found"
            )
        
        # Get the setting
        setting = db.query(StrategySetting).filter(
            StrategySetting.strategy_id == strategy_id,
            StrategySetting.setting_key == setting_key
        ).first()
        
        if not setting:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Setting '{setting_key}' not found for strategy {strategy_id}"
            )
        
        parsed_value = strategy_settings_service._parse_setting_value(
            setting.setting_value, setting.setting_type
        )
        
        return {
            "key": setting.setting_key,
            "value": parsed_value,
            "type": setting.setting_type.value,
            "description": setting.description,
            "default_value": strategy_settings_service._parse_setting_value(
                setting.default_value, setting.setting_type
            ) if setting.default_value else None,
            "is_required": setting.is_required,
            "created_at": setting.created_at.isoformat(),
            "updated_at": setting.updated_at.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting setting {setting_key} for strategy {strategy_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get strategy setting"
        )

@router.put("/{strategy_id}/settings/{setting_key}")
async def update_strategy_setting(
    strategy_id: int, 
    setting_key: str, 
    setting_request: SettingRequest,
    db: Session = Depends(get_db)
):
    """Update or create a specific setting for a strategy"""
    try:
        # Check if strategy exists
        strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
        if not strategy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Strategy {strategy_id} not found"
            )
        
        # Update the setting
        success = strategy_settings_service.set_setting(
            db=db,
            strategy_id=strategy_id,
            setting_key=setting_key,
            value=setting_request.value,
            setting_type=setting_request.setting_type,
            description=setting_request.description or "",
            default_value=setting_request.value,  # Use current value as default
            is_required=setting_request.is_required or False
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update strategy setting"
            )
        
        # Return the updated setting
        return await get_strategy_setting(strategy_id, setting_key, db)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating setting {setting_key} for strategy {strategy_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update strategy setting"
        )

@router.delete("/{strategy_id}/settings/{setting_key}")
async def delete_strategy_setting(strategy_id: int, setting_key: str, db: Session = Depends(get_db)):
    """Delete a specific setting for a strategy"""
    try:
        # Check if strategy exists
        strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
        if not strategy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Strategy {strategy_id} not found"
            )
        
        # Delete the setting
        success = strategy_settings_service.delete_setting(db, strategy_id, setting_key)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Setting '{setting_key}' not found for strategy {strategy_id}"
            )
        
        return {"message": f"Setting '{setting_key}' deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting setting {setting_key} for strategy {strategy_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete strategy setting"
        )

@router.post("/{strategy_id}/settings/initialize")
async def initialize_default_settings(strategy_id: int, db: Session = Depends(get_db)):
    """Initialize default settings for a strategy based on its type"""
    try:
        # Check if strategy exists
        strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
        if not strategy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Strategy {strategy_id} not found"
            )
        
        # Initialize default settings
        success = strategy_settings_service.initialize_default_settings(
            db, strategy_id, strategy.strategy_type.value
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to initialize default settings"
            )
        
        # Return the initialized settings
        return await get_strategy_settings(strategy_id, db)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error initializing settings for strategy {strategy_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initialize default settings"
        )

@router.get("/{strategy_id}/settings/defaults")
async def get_default_settings_template(strategy_id: int, db: Session = Depends(get_db)):
    """Get the default settings template for a strategy type"""
    try:
        # Check if strategy exists
        strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
        if not strategy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Strategy {strategy_id} not found"
            )
        
        # Get default settings template
        defaults = strategy_settings_service._get_default_settings_for_type(
            strategy.strategy_type.value
        )
        
        return {
            "strategy_id": strategy_id,
            "strategy_type": strategy.strategy_type.value,
            "default_settings": defaults
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting default settings for strategy {strategy_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get default settings template"
        )