from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.models.user_settings import UserSettings
from src.config import settings

async def get_or_create_settings(db: AsyncSession, user_id: int) -> UserSettings:
    result = await db.execute(
        select(UserSettings).where(UserSettings.user_id == user_id)
    )
    settings_record = result.scalar_one_or_none()
    
    if not settings_record:
        settings_record = UserSettings(
            user_id=user_id,
            api_key="",
            api_url="",
            default_model=""
        )
        db.add(settings_record)
        await db.commit()
        await db.refresh(settings_record)
    
    return settings_record

async def get_user_llm_config(db: AsyncSession, user_id: int) -> dict:
    user_settings = await get_or_create_settings(db, user_id)
    
    return {
        "api_key": user_settings.api_key or "",
        "api_url": user_settings.api_url or settings.DEFAULT_API_URL,
        "model": user_settings.default_model or settings.DEFAULT_MODEL
    }
