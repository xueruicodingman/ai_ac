from pydantic import BaseModel
from typing import Optional

class UserSettingsUpdate(BaseModel):
    api_key: Optional[str] = None
    api_url: Optional[str] = None
    default_model: Optional[str] = None
    theme: Optional[str] = None

class UserSettingsResponse(BaseModel):
    api_key: Optional[str]
    api_url: Optional[str]
    default_model: Optional[str]
    theme: Optional[str]
    default_api_url: str
    default_model_name: str
