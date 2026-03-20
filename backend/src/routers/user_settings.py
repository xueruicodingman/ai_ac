from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_db
from src.models.user import User
from src.routers.auth import get_current_user
from src.schemas.user_settings import UserSettingsUpdate, UserSettingsResponse
from src.services.user_settings_service import get_or_create_settings
from src.config import settings

router = APIRouter(prefix="/api/user/settings", tags=["用户设置"])

@router.get("", response_model=UserSettingsResponse)
async def get_settings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    user_settings = await get_or_create_settings(db, current_user.id)
    
    return UserSettingsResponse(
        api_key=user_settings.api_key,
        api_url=user_settings.api_url or "",
        default_model=user_settings.default_model or "",
        theme=user_settings.theme,
        default_api_url=settings.DEFAULT_API_URL,
        default_model_name=settings.DEFAULT_MODEL
    )

@router.put("", response_model=UserSettingsResponse)
async def update_settings(
    data: UserSettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    user_settings = await get_or_create_settings(db, current_user.id)
    
    if data.api_key is not None:
        user_settings.api_key = data.api_key
    if data.api_url is not None:
        user_settings.api_url = data.api_url
    if data.default_model is not None:
        user_settings.default_model = data.default_model
    if data.theme is not None:
        user_settings.theme = data.theme
    
    await db.commit()
    await db.refresh(user_settings)
    
    return UserSettingsResponse(
        api_key=user_settings.api_key,
        api_url=user_settings.api_url or "",
        default_model=user_settings.default_model or "",
        theme=user_settings.theme,
        default_api_url=settings.DEFAULT_API_URL,
        default_model_name=settings.DEFAULT_MODEL
    )
