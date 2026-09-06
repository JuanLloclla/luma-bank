from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "luma-bank-ai-service"
    app_env: str = "development"
    similarity_threshold: float = 0.50

    class Config:
        env_file = ".env"

settings = Settings()