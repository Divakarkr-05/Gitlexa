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

    # GitHub App Integration (Gitlexa's-AI)
    GITHUB_APP_ID: Optional[str] = None
    GITHUB_INSTALLATION_ID: Optional[int] = None
    GITHUB_APP_PRIVATE_KEY: Optional[SecretStr] = None
    GITHUB_APP_PRIVATE_KEY_PATH: Optional[str] = None
    GITHUB_APP_SECRET_REF: Optional[str] = None
    GITHUB_CLIENT_ID: Optional[str] = None
    GITHUB_CLIENT_SECRET: Optional[SecretStr] = None
    GITHUB_APP_NAME: str = "Gitlexa's-AI"
    GITHUB_APP_SLUG: str = "gitlexa-s-ai"
    FRONTEND_URL: str = "http://localhost:5173"

    # AWS & Amazon Bedrock Configuration
    AWS_REGION: str = "ap-southeast-2"
    AWS_ACCESS_KEY_ID: Optional[SecretStr] = None
    AWS_SECRET_ACCESS_KEY: Optional[SecretStr] = None
    BEDROCK_MODEL_ID: str = "amazon.nova-micro-v1:0"

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    def get_github_token_value(self) -> Optional[str]:
        """Safely expose the raw token string only when explicitly needed by clients."""
        return self.GITHUB_TOKEN.get_secret_value() if self.GITHUB_TOKEN else None

    def get_github_app_private_key_value(self) -> Optional[str]:
        """Safely expose the raw GitHub App private key only when needed for JWT signing."""
        return self.GITHUB_APP_PRIVATE_KEY.get_secret_value() if self.GITHUB_APP_PRIVATE_KEY else None

    def get_github_client_secret_value(self) -> Optional[str]:
        """Safely expose the GitHub App client secret."""
        return self.GITHUB_CLIENT_SECRET.get_secret_value() if self.GITHUB_CLIENT_SECRET else None

    def is_github_app_configured(self) -> bool:
        """Check whether minimum GitHub App credentials are provided."""
        has_id = bool(self.GITHUB_APP_ID and str(self.GITHUB_APP_ID).strip())
        has_key = bool(
            self.GITHUB_APP_PRIVATE_KEY
            or self.GITHUB_APP_PRIVATE_KEY_PATH
            or self.GITHUB_APP_SECRET_REF
        )
        return has_id and has_key

    def get_github_app_install_url(self) -> str:
        """Construct official GitHub App installation URL."""
        slug = (self.GITHUB_APP_SLUG or "gitlexa-s-ai").strip().strip("/")
        return f"https://github.com/apps/{slug}/installations/new"

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
