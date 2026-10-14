from functools import lru_cache
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "VoiceStudio"
    app_version: str = "1.0.0"
    debug: bool = False
    environment: str = "development"

    # Server
    host: str = "127.0.0.1"
    port: int = 8000

    # Database
    database_url: str = "sqlite+aiosqlite:///./voicestudio.db"

    # Security
    secret_key: str = Field(default="dev-secret-change-in-production-min-32-chars-long", min_length=32)
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # CORS
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173", "http://127.0.0.1:5173"])

    # OIDC / Keycloak
    oidc_enabled: bool = False
    oidc_issuer_url: Optional[str] = None
    oidc_client_id: Optional[str] = None
    oidc_client_secret: Optional[str] = None
    oidc_redirect_uri: Optional[str] = None
    oidc_scopes: list[str] = Field(default_factory=lambda: ["openid", "profile", "email"])

    # LLM (optional)
    llm_api_key: Optional[str] = None
    llm_provider: str = "openai-compatible"
    llm_model: Optional[str] = None
    llm_base_url: Optional[str] = None

    # Audio
    audio_sample_rate: int = 22050
    audio_output_format: str = "wav"
    max_text_length: int = 5000

    # File storage
    upload_dir: str = "./uploads"
    max_upload_size_mb: int = 50


@lru_cache
def get_settings() -> Settings:
    return Settings()