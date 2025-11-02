from pydantic_settings import BaseSettings
from typing import List, Optional

class Settings(BaseSettings):
    API_PREFIX: str = "/api"
    CORS_ORIGINS: List[str] = ["http://localhost:8501", "http://127.0.0.1:8501"]
    DATABASE_URL: Optional[str] = None  # e.g. "postgresql+asyncpg://user:password@localhost/dbname"

    class Config:
        env_file = ".env"  

settings = Settings()
