"""
Configuration principale de ChicoBot.

Gestion centralisée des paramètres avec Pydantic pour validation.
Support des variables d'environnement et configuration par défaut.
"""

import os
from typing import Optional

from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """Configuration principale de ChicoBot."""
    
    # Configuration Telegram
    telegram_token: str = Field(..., env="TELEGRAM_TOKEN")
    telegram_api_id: Optional[int] = Field(None, env="TELEGRAM_API_ID")
    telegram_api_hash: Optional[str] = Field(None, env="TELEGRAM_API_HASH")
    
    # Configuration Base de Données
    database_url: str = Field("sqlite:///chicobot.db", env="DATABASE_URL")
    database_pool_size: int = Field(10, env="DATABASE_POOL_SIZE")
    
    # Configuration APIs Externes
    serpapi_key: Optional[str] = Field(None, env="SERPAPI_KEY")
    openai_api_key: Optional[str] = Field(None, env="OPENAI_API_KEY")
    gemini_api_key: Optional[str] = Field(None, env="GEMINI_API_KEY")
    
    # Configuration Trading
    mt5_login: Optional[int] = Field(None, env="MT5_LOGIN")
    mt5_password: Optional[str] = Field(None, env="MT5_PASSWORD")
    mt5_server: Optional[str] = Field(None, env="MT5_SERVER")
    
    # Configuration Sécurité
    encryption_key: str = Field(..., env="ENCRYPTION_KEY")
    jwt_secret: str = Field(..., env="JWT_SECRET")
    
    # Configuration Foundation
    foundation_wallet: str = Field("chico_foundation_treasury", env="FOUNDATION_WALLET")
    foundation_rate: float = Field(0.01, env="FOUNDATION_RATE")
    
    # Configuration Admin
    max_admins: int = Field(3, env="MAX_ADMINS")
    admin_commission_rate: float = Field(0.02, env="ADMIN_COMMISSION_RATE")
    
    # Configuration Logging
    log_level: str = Field("INFO", env="LOG_LEVEL")
    log_file: Optional[str] = Field(None, env="LOG_FILE")
    
    # Configuration Performance
    cache_ttl: int = Field(3600, env="CACHE_TTL")
    max_concurrent_tasks: int = Field(100, env="MAX_CONCURRENT_TASKS")
    
    # Configuration Environnement
    environment: str = Field("development", env="ENVIRONMENT")
    debug: bool = Field(False, env="DEBUG")
    
    class Config:
        """Configuration Pydantic."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Instance globale des settings
settings = Settings()
