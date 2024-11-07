from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # JWT Settings
    JWT_SECRET: str = "1892dhianiandowqd0n"
    JWT_ALG: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Database Settings
    DATABASE_URL: str = "sqlite:///news_database.db"
    
    # CORS Settings
    CORS_ORIGINS: List[str] = ["http://localhost:8080"]
    
    # OpenAI Settings
    OPENAI_API_KEY: str = "xxx"
    
    # Sentry Settings
    SENTRY_DSN: str = "https://4001ffe917ccb261aa0e0c34026dc343@o4505702629834752.ingest.us.sentry.io/4507694792704000"

    class Config:
        env_file = ".env"

settings = Settings() 