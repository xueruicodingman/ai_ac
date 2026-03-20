from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    APP_NAME: str = "AC测评工具"
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7
    
    DATABASE_URL: str = "sqlite+aiosqlite:///./ac_assessment.db"
    
    UPLOAD_DIR: str = "./uploads"
    GENERATED_DIR: str = "./generated"
    
    DEFAULT_API_URL: str = "https://api.openai.com/v1"
    DEFAULT_MODEL: str = "gpt-4"
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()
