"""
Package de configuration de ChicoBot.

Centralise tous les paramètres et constantes utilisés dans l'application.
"""

from .constants import *
from .settings import settings

__all__ = [
    "settings",
    # Constantes principales
    "CREATORS_PRAISE_MESSAGE",
    "FOUNDATION_MESSAGE",
    "FOUNDATION_RATE",
    "MAX_ADMINS",
    "ADMIN_COMMISSION_RATE",
    # Messages et états
    "HELP_TEXT",
    "PALIER_MESSAGES",
    "WELCOME_MESSAGE",
    # États FSM
    "WalletStates",
    "BountyStates",
    "WithdrawalStates",
    "AdminQuizStates",
]

logger = get_logger(__name__)
logger.info("Package configuration chargé")
