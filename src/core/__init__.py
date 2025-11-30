"""
Package core de ChicoBot.

Contient les modules fondamentaux :
- Base de données avec SQLAlchemy async
- Sécurité avec chiffrement post-quantique
- Service IA avec Gemini et GPT-4
- Logging avancé avec monitoring
"""

from .database import database
from .logging_setup import get_logger
from .security import WalletSecurityManager
from .ai_service import ai_service, get_ai_service

__all__ = [
    "database",
    "get_logger",
    "WalletSecurityManager",
    "ai_service",
    "get_ai_service",
]

logger = get_logger(__name__)
logger.info("Package core initialisé")
