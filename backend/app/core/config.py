"""Configuration management for Gitlexa.

Owned by Member 01 (Cloud, Security & DevOps).
Reads settings from environment variables and .env files safely.
Never hardcodes secrets or credentials.
"""

from typing import List, Optional
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable bindings."""

    # Project Information
    PROJECT_NAME: str = "Gitlexa"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    API_V1_STR: str = "/api/v1"

    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]

    # Security & API Authentication (Optional header-based key)
    API_KEY: Optional[SecretStr] = None

    # GitHub Credentials (Read strictly from env, never hardcoded)
    GITHUB_TOKEN: Optional[SecretStr] = None

    # AWS & Amazon Bedrock Configuration
    AWS_REGION: str = "ap-southeast-2"
    AWS_ACCESS_KEY_ID: Optional[SecretStr] = None
    AWS_SECRET_ACCESS_KEY: Optional[SecretStr] = None
    BEDROCK_MODEL_ID: str = "amazon.nova-micro-v1:0"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    def get_github_token_value(self) -> Optional[str]:
        """Safely expose the raw token string only when explicitly needed by clients."""
        return self.GITHUB_TOKEN.get_secret_value() if self.GITHUB_TOKEN else None

    def get_aws_access_key(self) -> Optional[str]:
        """Safely expose the AWS access key value."""
        return self.AWS_ACCESS_KEY_ID.get_secret_value() if self.AWS_ACCESS_KEY_ID else None

    def get_aws_secret_key(self) -> Optional[str]:
        """Safely expose the AWS secret access key value."""
        return self.AWS_SECRET_ACCESS_KEY.get_secret_value() if self.AWS_SECRET_ACCESS_KEY else None

    def get_api_key_value(self) -> Optional[str]:
        """Safely expose the API key value."""
        return self.API_KEY.get_secret_value() if self.API_KEY else None


# Global settings instance
settings = Settings()
