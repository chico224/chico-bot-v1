"""
Package handlers de ChicoBot.

Contient tous les handlers de commandes et messages Telegram.
TOUTES les réponses passent par le moteur de personnalité Chico.
"""

from .commands import router as commands_router
from .chico_handlers import ChicoHandlers, get_chico_handlers

__all__ = [
    "commands_router",
    "ChicoHandlers", 
    "get_chico_handlers"
]

logger = get_logger(__name__)
logger.info("Package handlers chargé - Mode Chico Personality activé 🇬🇳")
