# File: agentic_rental_platform/app/core/config.py

from typing import List, Optional, Union
from pydantic import AnyHttpUrl, PostgresDsn, RedisDsn, field_validator, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
import os

class Settings(BaseSettings):
    # Application Settings
    APP_NAME: str = Field("Agentic Rental Platform", examples=["My Awesome App"])
    ENVIRONMENT: str = Field("development", examples=["development", "staging", "production"])
    DEBUG: bool = Field(True)
    API_V1_STR: str = Field("/api/v1", examples=["/api/v1"])
    SECRET_KEY: str = Field("your_super_secret_and_long_random_key_here_in_config_default")

    # Project Paths
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    # CORS (Cross-Origin Resource Sharing)
    BACKEND_CORS_ORIGINS_STR: str = Field("http://localhost:3000,http://localhost:8080,http://127.0.0.1:3000,http://127.0.0.1:8080")
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]], info) -> Union[List[str], str]: # Changed 'values' to 'info' for Pydantic v2
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(f"Invalid BACKEND_CORS_ORIGINS value: {v}")

    # PostgreSQL Database
    POSTGRES_USER: str = Field("your_db_user")
    POSTGRES_PASSWORD: str = Field("your_db_password")
    POSTGRES_SERVER: str = Field("localhost")
    POSTGRES_PORT: str = Field("5432")
    POSTGRES_DB: str = Field("agentic_rental_db")
    DATABASE_URL: Optional[PostgresDsn] = None

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: Optional[str], info) -> Optional[PostgresDsn]: # Changed 'values' to 'info'
        if isinstance(v, str):
            return PostgresDsn(v) # Validate if set directly
        
        data = info.data # Access other field values via info.data
        user = data.get("POSTGRES_USER")
        password = data.get("POSTGRES_PASSWORD")
        server = data.get("POSTGRES_SERVER")
        port = data.get("POSTGRES_PORT")
        db_name = data.get("POSTGRES_DB")
        URL = data.get("DATABASE_URL")

        if not all([user, password, server, port, db_name]):
            # If any component is missing and DATABASE_URL isn't set directly, this will be an issue.
            # Pydantic will raise validation error if DATABASE_URL ends up being None and is not Optional.
            # Making DATABASE_URL Optional allows it to be None if components are missing.
            # Alternatively, raise ValueError here if components are expected.
            return None # Or raise ValueError("DB components missing and DATABASE_URL not set")
        
        return PostgresDsn(f"postgresql+asyncpg://{user}:{password}@{server}:{port}/{db_name}")
        return PostgresDsn(URL)

    # Redis
    REDIS_HOST: str = Field("localhost")
    REDIS_PORT: str = Field("6379")
    REDIS_DB: int = Field(0)
    REDIS_PASSWORD: Optional[str] = Field(None)
    REDIS_URL: Optional[RedisDsn] = None

    @field_validator("REDIS_URL", mode="before")
    @classmethod
    def assemble_redis_connection(cls, v: Optional[str], info) -> Optional[RedisDsn]: # Changed 'values' to 'info'
        if isinstance(v, str):
            return RedisDsn(v)
        
        data = info.data
        host = data.get("REDIS_HOST")
        port = data.get("REDIS_PORT")
        db = data.get("REDIS_DB")
        password = data.get("REDIS_PASSWORD")

        if password:
            return RedisDsn(f"redis://:{password}@{host}:{port}/{db}")
        return RedisDsn(f"redis://{host}:{port}/{db}")

    # Celery Broker (using Redis)
    CELERY_BROKER_URL: str = Field("redis://localhost:6379/1")
    CELERY_RESULT_BACKEND: str = Field("redis://localhost:6379/2")

    # AI Services API Keys
    OPENAI_API_KEY: Optional[str] = Field(None)
    DEEPSEEK_API_KEY: Optional[str] = Field(None)
    HUGGINGFACE_API_TOKEN: Optional[str] = Field(None)
    OPENAI_BASE_URL: Optional[AnyHttpUrl] = Field(None)
    DEEPSEEK_BASE_URL: Optional[AnyHttpUrl] = Field(None)

    # JWT Token Settings
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(30)
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(7)
    ALGORITHM: str = Field("HS256")
    JWT_SECRET_KEY: Optional[str] = Field(None) # If None, will use SECRET_KEY
    JWT_REFRESH_SECRET_KEY: Optional[str] = Field(None) # If None, will use SECRET_KEY + "_refresh"

    @field_validator("JWT_SECRET_KEY", mode="before")
    @classmethod
    def assemble_jwt_secret(cls, v: Optional[str], info) -> str: # Changed 'values' to 'info'
        if v:
            return v
        secret_key = info.data.get("SECRET_KEY")
        if not secret_key:
            raise ValueError("SECRET_KEY must be set if JWT_SECRET_KEY is not.")
        return secret_key
        
    @field_validator("JWT_REFRESH_SECRET_KEY", mode="before")
    @classmethod
    def assemble_jwt_refresh_secret(cls, v: Optional[str], info) -> str: # Changed 'values' to 'info'
        if v:
            return v
        jwt_secret = info.data.get("JWT_SECRET_KEY") # Should use already processed JWT_SECRET_KEY
        if not jwt_secret: # This case should be caught by JWT_SECRET_KEY validator if SECRET_KEY is also missing
             # Fallback to SECRET_KEY directly if JWT_SECRET_KEY logic somehow didn't populate
            jwt_secret = info.data.get("SECRET_KEY")
            if not jwt_secret:
                 raise ValueError("SECRET_KEY or JWT_SECRET_KEY must be set for JWT_REFRESH_SECRET_KEY default.")
        return jwt_secret + "_refresh"


    # Feature Flags
    FEATURE_ADVANCED_SEARCH_ENABLED: bool = Field(False)
    FEATURE_NEW_RECOMMENDATION_ALGORITHM_ENABLED: bool = Field(False)

    # GDPR Compliance Settings
    DATA_RETENTION_PERIOD_DAYS: int = Field(365)
    PRIVACY_POLICY_URL: Optional[AnyHttpUrl] = Field(None)
    COOKIE_CONSENT_ENABLED: bool = Field(True)

    # SMTP Settings for Email
    SMTP_TLS: bool = Field(True)
    SMTP_PORT: Optional[int] = Field(None)
    SMTP_HOST: Optional[str] = Field(None)
    SMTP_USER: Optional[str] = Field(None)
    SMTP_PASSWORD: Optional[str] = Field(None)
    EMAILS_FROM_EMAIL: Optional[str] = Field(None)
    EMAILS_FROM_NAME: Optional[str] = Field(None)

    @field_validator("EMAILS_FROM_NAME", mode="before")
    @classmethod
    def assemble_emails_from_name(cls, v: Optional[str], info) -> Optional[str]: # Changed 'values' to 'info'
        if v:
            return v
        return info.data.get("APP_NAME")

    # Logging Configuration
    LOG_LEVEL: str = Field("INFO", examples=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False # Environment variables are often uppercase
    )

settings = Settings()