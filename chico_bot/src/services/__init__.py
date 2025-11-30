"""
Package services de ChicoBot.

Contient tous les services métier :
- Gestion des bounties cryptos
- Trading quantitatif de niveau institutionnel
- Investissements style milliardaires
- Sécurité niveau militaire
- Système admin ultra-sécurisé
- Chico Foundation - 1% pour la charité
"""

from .admin_system import admin_router, admin_system
from .bounty_service import bounty_service
from .foundation_service import chico_foundation, foundation_router
from .fortress_security import fortress_security
from .investment_service import investment_engine
from .trading_service import trading_engine

__all__ = [
    "admin_router",
    "admin_system",
    "bounty_service",
    "chico_foundation",
    "foundation_router",
    "fortress_security",
    "investment_engine",
    "trading_engine",
]

logger = get_logger(__name__)
logger.info("Package services initialisé")
