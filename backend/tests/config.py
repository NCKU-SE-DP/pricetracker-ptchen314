from pydantic_settings import BaseSettings
import os 

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///news_database.db"
    SECRET_KEY: str = "1892dhianiandowqd0n"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    OPENAI_API_KEY: str = f"{os.getenv('OPENAI_API_KEY')}"
    OPENAI_MODEL: str = f"{os.getenv('OPENAI_MODEL')}"
    ANTHROPIC_API_KEY: str = f"{os.getenv('ANTHROPIC_API_KEY')}"
    ANTHROPIC_MODEL: str = f"{os.getenv('ANTHROPIC_MODEL')}"
    SENTRY_DSN: str = f"{os.getenv('SENTRY_DSN')}"
    CORS_ORIGINS: list = ["http://localhost:8080"]

settings = Settings() 