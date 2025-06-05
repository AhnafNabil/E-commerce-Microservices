import os
from typing import Optional

from pydantic import BaseSettings, validator, PostgresDsn


class Settings(BaseSettings):
    # API settings
    API_PREFIX: str = "/api/v1"
    DEBUG: bool = False
    PROJECT_NAME: str = "User Service"
    PORT: int = 8003
    
    # Database settings
    DATABASE_URL: PostgresDsn
    
    # JWT settings
    JWT_SECRET_KEY: str = "your-super-secret-key-here-change-it-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Security
    SECURITY_PASSWORD_SALT: str = "your-password-salt-change-it-in-production"
    SECURITY_PASSWORD_HASH: str = "bcrypt"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Create global settings object
settings = Settings()