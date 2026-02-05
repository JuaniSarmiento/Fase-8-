"""
Configuration using Pydantic Settings
"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings from environment variables."""
    
    # App
    APP_NAME: str = "AI-Native MVP V3"
    APP_VERSION: str = "3.0.0"
    DEBUG: bool = False  # CHANGED: False por defecto para seguridad
    ENVIRONMENT: str = "development"  # development, staging, production
    
    # Database
    DATABASE_URL: str
    
    # Redis
    REDIS_URL: str = "redis://redis:6379/0"
    REDIS_MAX_CONNECTIONS: int = 50
    REDIS_SOCKET_TIMEOUT: int = 5
    REDIS_SOCKET_CONNECT_TIMEOUT: int = 5
    REDIS_RETRY_ON_TIMEOUT: bool = True
    
    # Security
    SECRET_KEY: str = "CHANGE_ME_IN_PRODUCTION"  # Legacy, usar JWT_SECRET_KEY
    JWT_SECRET_KEY: str = ""  # REQUIRED: Generate with: python -c 'import secrets; print(secrets.token_hex(32))'
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    
    # CORS - CRITICAL: Only allow specific domains in production
    ALLOWED_ORIGINS: str = "http://localhost:3000"  # Comma-separated list
    
    # LLM
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-3-5-sonnet-20241022"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2:latest"
    
    # Mistral AI - REQUIRED for tutor functionality
    MISTRAL_API_KEY: str = ""
    MISTRAL_MODEL: str = "mistral-small-latest"
    MISTRAL_TEMPERATURE: str = "0.7"
    MISTRAL_MAX_TOKENS: str = "2048"
    MISTRAL_TIMEOUT: str = "60"
    MISTRAL_MAX_RETRIES: str = "3"
    
    # LangSmith
    LANGCHAIN_TRACING_V2: bool = False
    LANGCHAIN_API_KEY: str = ""
    LANGCHAIN_PROJECT: str = "ai-native-mvp-v3"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    @property
    def allowed_origins_list(self) -> List[str]:
        """Parse ALLOWED_ORIGINS into list."""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]


def get_settings() -> Settings:
    """Get settings instance."""
    return settings


# Global settings instance
settings = Settings()
