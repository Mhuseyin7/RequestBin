from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    database_url: str = "postgresql+asyncpg://requestbinx:requestbinx@postgres:5432/requestbinx"
    jwt_secret: str = Field(min_length=32, default="change-this-development-secret-before-deploying")
    cors_origins: str = "http://localhost:3000"
    max_body_bytes: int = 1_048_576
    allow_unsafe_outbound: bool = False
    anonymous_bins_enabled: bool = False
    body_storage_path: str = "/data/bodies"

@lru_cache
def get_settings() -> Settings:
    return Settings()
