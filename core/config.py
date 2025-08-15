from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Core settings
    SECRET_KEY: str = "a_very_secret_key_that_should_be_changed"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # URLs
    BASE_URL: str = "http://localhost:8003"  # Updated to match test expectations
    FRONTEND_URL: str = "http://localhost:3000"
    
    # Database settings
    MONGO_URI: str = "mongodb://localhost:27017/"

    # Redis settings
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379

    # Facebook App settings
    FB_APP_ID: str = ""
    FB_APP_SECRET: str = ""
    FB_GRAPH_API_VERSION: str = "v19.0"
    
    # Facebook Webhook settings
    FACEBOOK_WEBHOOK_SECRET: str = ""
    FACEBOOK_WEBHOOK_VERIFY_TOKEN: str = "realestate_ai_webhook_verify"

    # API keys
    GROQ_API_KEY: str
    FB_PAGE_ID: str
    FB_PAGE_TOKEN: str
    AI_DISABLE_IMAGE_GENERATION: bool = True
    
    # Optional external API keys
    STABILITY_API_KEY: str = ""
    HUGGINGFACE_API_TOKEN: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'

settings = Settings()
