import os
from typing import Optional, List

from pydantic import BaseSettings, AnyHttpUrl, EmailStr, validator, PostgresDsn


class Settings(BaseSettings):
    # API settings
    API_PREFIX: str = "/api/v1"
    DEBUG: bool = False
    PROJECT_NAME: str = "User Service"
    PORT: int = 8000
    
    # Database settings
    DATABASE_URL: PostgresDsn
    
    # JWT settings
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Security
    SECURITY_PASSWORD_SALT: str
    SECURITY_PASSWORD_HASH: str = "bcrypt"
    
    # Email settings
    MAIL_SERVER: str
    MAIL_PORT: int = 587
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: EmailStr
    MAIL_TLS: bool = True
    MAIL_SSL: bool = False
    MAIL_FROM_NAME: str
    
    # URL settings
    VERIFY_EMAIL_URL: AnyHttpUrl
    RESET_PASSWORD_URL: AnyHttpUrl
    
    # Feature flags
    ENABLE_EMAIL_VERIFICATION: bool = False
    
    # User roles
    USER_ROLES: List[str] = ["user", "admin"]
    
    # Validate URLs are properly formatted
    @validator("VERIFY_EMAIL_URL", "RESET_PASSWORD_URL", pre=True)
    def validate_urls(cls, v):
        if isinstance(v, str) and not v.startswith(("http://", "https://")):
            return f"http://{v}"
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Create global settings object
settings = Settings()