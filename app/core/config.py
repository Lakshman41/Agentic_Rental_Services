# File: agentic_rental_platform/app/core/config.py
from typing import List, Optional, Union
from pydantic import AnyHttpUrl, PostgresDsn, RedisDsn, field_validator, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
import os

class Settings(BaseSettings):
    APP_NAME: str = Field("Agentic Rental Platform")
    ENVIRONMENT: str = Field("development")
    DEBUG: bool = Field(True)
    API_V1_STR: str = Field("/api/v1")
    SECRET_KEY: str = Field("please_change_me_in_production_to_a_very_strong_secret") # Ensure this is strong in .env

    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    BACKEND_CORS_ORIGINS_STR: str = Field("http://localhost:3000,http://localhost:8080,http://127.0.0.1:3000,http://127.0.0.1:8080")
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]], info) -> List[AnyHttpUrl]:
        if isinstance(v, str) and not v.startswith("["):
            return [AnyHttpUrl(i.strip()) for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return [AnyHttpUrl(i) for i in v]
        elif isinstance(v, str) and v.startswith("["): # Handles stringified list
             import json
             try:
                 return [AnyHttpUrl(i) for i in json.loads(v)]
             except json.JSONDecodeError:
                 raise ValueError(f"Invalid stringified list for BACKEND_CORS_ORIGINS: {v}")
        raise ValueError(f"Invalid BACKEND_CORS_ORIGINS value: {v}")

    POSTGRES_USER: Optional[str] = Field("your_db_user")
    POSTGRES_PASSWORD: Optional[str] = Field("your_db_password_here")
    POSTGRES_SERVER: Optional[str] = Field("localhost")
    POSTGRES_PORT: Optional[str] = Field("5432")
    POSTGRES_DB: Optional[str] = Field("agentic_rental_db")
    DATABASE_URL: Optional[PostgresDsn] = None # Will be assembled if components are set

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: Optional[str], info) -> Optional[PostgresDsn]:
        if v: # If DATABASE_URL is set directly in .env, use it
            return PostgresDsn(v)
        
        data = info.data
        user = data.get("POSTGRES_USER")
        password = data.get("POSTGRES_PASSWORD")
        server = data.get("POSTGRES_SERVER")
        port = data.get("POSTGRES_PORT")
        db_name = data.get("POSTGRES_DB")
        URL=data.get("DATABASE_URL")

        if all([user, password, server, port, db_name]):
            return PostgresDsn(f"postgresql+asyncpg://{user}:{password}@{server}:{port}/{db_name}")
        return URL # If components are not fully set and DATABASE_URL isn't directly provided

    REDIS_HOST: str = Field("localhost")
    REDIS_PORT: str = Field("6379")
    REDIS_DB: int = Field(0)
    REDIS_PASSWORD: Optional[str] = Field(None)
    REDIS_URL: Optional[RedisDsn] = None

    @field_validator("REDIS_URL", mode="before")
    @classmethod
    def assemble_redis_connection(cls, v: Optional[str], info) -> Optional[RedisDsn]:
        if v:
            return RedisDsn(v)
        data = info.data
        host, port_str, db_str = data.get("REDIS_HOST"), data.get("REDIS_PORT"), str(data.get("REDIS_DB", 0))
        password = data.get("REDIS_PASSWORD")
        if not all([host, port_str, db_str is not None]): return None # Ensure basic components
        
        port = int(port_str)
        db = int(db_str)

        if password:
            return RedisDsn(f"redis://:{password}@{host}:{port}/{db}")
        return RedisDsn(f"redis://{host}:{port}/{db}")

    CELERY_BROKER_URL: str = Field("redis://localhost:6379/1")
    CELERY_RESULT_BACKEND: str = Field("redis://localhost:6379/2")

    OPENAI_API_KEY: Optional[str] = Field(None)
    DEEPSEEK_API_KEY: Optional[str] = Field(None)
    HUGGINGFACE_API_TOKEN: Optional[str] = Field(None)
    OPENAI_BASE_URL: Optional[AnyHttpUrl] = Field(None)
    DEEPSEEK_BASE_URL: Optional[AnyHttpUrl] = Field(None)

    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(30)
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(7)
    ALGORITHM: str = Field("HS256")
    JWT_SECRET_KEY: Optional[str] = Field(None)
    JWT_REFRESH_SECRET_KEY: Optional[str] = Field(None)

    @field_validator("JWT_SECRET_KEY", mode="before")
    @classmethod
    def assemble_jwt_secret(cls, v: Optional[str], info) -> str:
        if v: return v
        secret_key = info.data.get("SECRET_KEY")
        if not secret_key: raise ValueError("SECRET_KEY must be set if JWT_SECRET_KEY is not.")
        return secret_key
        
    @field_validator("JWT_REFRESH_SECRET_KEY", mode="before")
    @classmethod
    def assemble_jwt_refresh_secret(cls, v: Optional[str], info) -> str:
        if v: return v
        # Use already validated/defaulted JWT_SECRET_KEY if available in data, else re-evaluate SECRET_KEY
        jwt_secret = info.data.get("JWT_SECRET_KEY", info.data.get("SECRET_KEY"))
        if not jwt_secret: raise ValueError("SECRET_KEY or JWT_SECRET_KEY must be set for JWT_REFRESH_SECRET_KEY default.")
        return jwt_secret + "_refresh"

    FEATURE_ADVANCED_SEARCH_ENABLED: bool = Field(False)
    FEATURE_NEW_RECOMMENDATION_ALGORITHM_ENABLED: bool = Field(False)
    DATA_RETENTION_PERIOD_DAYS: int = Field(365)
    PRIVACY_POLICY_URL: Optional[AnyHttpUrl] = Field(None)
    COOKIE_CONSENT_ENABLED: bool = Field(True)

    SMTP_TLS: bool = Field(True)
    SMTP_PORT: Optional[int] = Field(None)
    SMTP_HOST: Optional[str] = Field(None)
    SMTP_USER: Optional[str] = Field(None)
    SMTP_PASSWORD: Optional[str] = Field(None)
    EMAILS_FROM_EMAIL: Optional[str] = Field(None)
    EMAILS_FROM_NAME: Optional[str] = Field(None)

    @field_validator("EMAILS_FROM_NAME", mode="before")
    @classmethod
    def assemble_emails_from_name(cls, v: Optional[str], info) -> Optional[str]:
        if v: return v
        return info.data.get("APP_NAME")

    LOG_LEVEL: str = Field("INFO")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False 
    )

settings = Settings()

# Ensure DATABASE_URL is actually usable after potential assembly
if not settings.DATABASE_URL:
    raise ValueError("Database configuration is incomplete. DATABASE_URL could not be assembled and was not set directly.")