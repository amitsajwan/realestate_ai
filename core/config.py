import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SECRET_KEY: str = os.getenv("SECRET_KEY", "changeme_this_is_not_secure")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    MODE: str = os.getenv("REAL_ESTATE_CRM_MODE", "production") # "production" or "development"
    MONGO_URI: str = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
    BASE_URL: str = os.getenv("BASE_URL", "http://localhost:8000")
    # ... add all other app configs (Facebook, AI keys, feature flags)

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'

settings = Settings()
