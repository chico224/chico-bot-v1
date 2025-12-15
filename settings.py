"""
Configuration principale de ChicoBot - Pydantic V2 Compatible

Gestion centralisée des paramètres avec Pydantic V2 pour validation.
Support des variables d'environnement et configuration par défaut.
"""

import os
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class Settings(BaseModel):
    """Configuration principale de ChicoBot - Pydantic V2."""
    
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        populate_by_name=True,
        str_strip_whitespace=True,
        strict=False
    )
    
    # Configuration Telegram
    telegram_bot_token: str = Field(..., alias="TELEGRAM_BOT_TOKEN")
    telegram_api_id: Optional[int] = Field(None, alias="TELEGRAM_API_ID")
    telegram_api_hash: Optional[str] = Field(None, alias="TELEGRAM_API_HASH")
    telegram_admin_chat_id: int = Field(..., alias="TELEGRAM_ADMIN_CHAT_ID")
    
    # Configuration Base de Données
    DATABASE_URL: str = Field("sqlite:///chicobot.db", alias="DATABASE_URL")
    LOG_LEVEL: int = Field(10, alias="DATABASE_POOL_SIZE")
    
    # Configuration APIs Externes
    serpapi_key: Optional[str] = Field(None, alias="SERPAPI_KEY")
    openai_project_api_key: Optional[str] = Field(None, alias="OPENAI_PROJECT_API_KEY")
    gemini_api_key: Optional[str] = Field(None, alias="GEMINI_API_KEY")
    
    # Configuration Trading MT5
    mt5_login: Optional[int] = Field(None, alias="MT5_LOGIN")
    mt5_password: Optional[str] = Field(None, alias="MT5_PASSWORD")
    mt5_server: Optional[str] = Field(None, alias="MT5_SERVER")
    
    # Configuration Wallet Utilisateur
    wallet_private_key: str = Field(..., alias="WALLET_PRIVATE_KEY")
    
    # Configuration Sécurité
    encryption_key: str = Field(..., alias="ENCRYPTION_KEY")
    jwt_secret: str = Field(..., alias="JWT_SECRET")
    
    # Configuration Foundation
    foundation_wallet: str = Field("0x...", alias="FOUNDATION_WALLET")
    foundation_rate: float = Field(0.01, alias="FOUNDATION_RATE")
    
    # Configuration Support Chico
    chico_whatsapp: str = Field("+224620000000", alias="CHICO_WHATSAPP")
    chico_call: str = Field("+224620000001", alias="CHICO_CALL")
    problematique_whatsapp: str = Field("+224620000002", alias="PROBLEMATIQUE_WHATSAPP")
    problematique_call: str = Field("+224620000003", alias="PROBLEMATIQUE_CALL")
    
    # Configuration Admin
    max_admins: int = Field(3, alias="MAX_ADMINS")
    admin_commission_rate: float = Field(0.02, alias="ADMIN_COMMISSION_RATE")
    
    # Configuration Logging
    log_level: str = Field("INFO", alias="LOG_LEVEL")
    log_file: Optional[str] = Field(None, alias="LOG_FILE")
    
    # Configuration Performance
    cache_ttl: int = Field(3600, alias="CACHE_TTL")
    max_concurrent_tasks: int = Field(100, alias="MAX_CONCURRENT_TASKS")
    
    # Configuration Environnement
    environment: str = Field("production", alias="ENVIRONMENT")
    debug: bool = Field(False, alias="DEBUG")


# Instance globale des settings - Pydantic V2
settings = Settings()

