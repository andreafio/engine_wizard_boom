"""Application configuration using Pydantic settings."""
import json
from typing import Dict, Literal
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Application
    app_env: Literal["dev", "prod"] = "dev"
    port: int = 8000
    host: str = "0.0.0.0"
    log_level: str = "INFO"
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    
    # Postgres (optional)
    database_url: str | None = None
    
    # Security
    tenant_keys_json: str = '{"boom":"API_KEY_123"}'
    hmac_secret: str = "change_me"
    
    # LLM
    llm_provider: Literal["openai", "gemini", "claude"] = "openai"
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-pro"
    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-3-sonnet-20240229"
    
    # Session
    session_ttl_seconds: int = 3600
    max_conversation_buffer: int = 10
    
    @field_validator("tenant_keys_json")
    @classmethod
    def validate_tenant_keys(cls, v: str) -> str:
        """Validate that tenant keys is valid JSON."""
        try:
            json.loads(v)
            return v
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON for tenant_keys_json: {e}")
    
    @property
    def tenant_keys(self) -> Dict[str, str]:
        """Parse tenant keys from JSON string."""
        return json.loads(self.tenant_keys_json)
    
    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.app_env == "prod"


# Global settings instance
settings = Settings()
