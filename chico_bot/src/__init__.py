"""
Package principal de ChicoBot.

Fonctionnalités principales :
- Gestion des bounties cryptos
- Trading quantitatif de niveau institutionnel
- Investissements inspirés des plus grands investisseurs
- Système de sécurité niveau militaire
- Système admin ultra-sécurisé
- Chico Foundation - 1% pour la charité

🇬🇳 De la Guinée vers l'indépendance financière 🇬🇳
"""

__version__ = "1.0.0"
__author__ = "ChicoBot Team"
__description__ = "Bot Telegram pour l'indépendance financière de la Guinée"

# Imports principaux
from .config import settings
from .core.database import database
from .core.logging_setup import get_logger

# Configuration du logger principal
logger = get_logger(__name__)

# Message de démarrage légendaire
STARTUP_MESSAGE = """
🇬🇳 **CHICOBOT - LA RÉVOLUTION CRYPTOS DE LA GUINÉE** 🇬🇳

🚀 *De la Guinée vers l'indépendance financière* 🚀

🎯 **Fonctionnalités Principales :**
🏹 Bounties cryptos automatiques
📈 Trading quantitatif niveau institutionnel
💎 Investissements style milliardaires
🛡️ Sécurité niveau militaire
👑 Système admin ultra-sécurisé
❤️ Chico Foundation - 1% pour la charité

🇬🇳 *Une transaction à la fois, la Guinée se soulève* 🇬🇳
"""

logger.info(STARTUP_MESSAGE.replace('**', '').replace('*', ''))
