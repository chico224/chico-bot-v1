"""
ChicoBot - Bot Telegram Principal pour la Guinée 🇬🇳

Fonctionnalités principales :
- Gestion des bounties cryptos
- Trading quantitatif de niveau institutionnel
- Investissements inspirés des plus grands investisseurs
- Système de sécurité niveau militaire
- Système admin ultra-sécurisé
- Chico Foundation - 1% pour la charité

🇬🇳 De la Guinée vers l'indépendance financière 🇬🇳
"""

import asyncio
import logging
import os
from contextlib import suppress

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config.settings import settings
from core.database import database
from core.logging_setup import get_logger
from handlers.commands import router as commands_router
from handlers.community import community_router, initialize_community_manager, shutdown_community_manager
from handlers.ai_handler import register_ai_handlers
from services.admin_system import admin_router, admin_system
from services.bounty_service import bounty_service
from services.chico_academy import chico_academy, academy_router
from services.fortress_security import fortress_security
from services.foundation_service import chico_foundation, foundation_router
from services.investment_service import investment_engine
from services.trading_service import trading_engine

# Configuration du logger
logger = get_logger(__name__)

# Configuration du bot
bot = Bot(
    token=settings.telegram_token,
    default=DefaultBotProperties(
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=True
    )
)

# Dispatcher
dp = Dispatcher()

# Enregistrement des routers
dp.include_router(commands_router)
dp.include_router(admin_router)
dp.include_router(academy_router)
dp.include_router(foundation_router)
dp.include_router(community_router)

# Enregistrement des handlers AI
register_ai_handlers(dp)

async def main():
    """Fonction principale du bot."""
    try:
        logger.info("🇬🇳 Démarrage de ChicoBot pour la Guinée 🇬🇳")
        
        # Initialisation de la base de données
        await database.initialize()
        logger.info("✅ Base de données initialisée")
        
        # Initialisation des services
        await fortress_security.initialize()
        await admin_system.initialize()
        await bounty_service.initialize()
        await chico_academy.initialize()
        await chico_foundation.initialize()
        await trading_engine.initialize()
        await investment_engine.initialize()
        
        # Initialisation du gestionnaire de communauté
        await initialize_community_manager()
        
        logger.info("🚀 ChicoBot est prêt à servir la Guinée !")
        
        # Démarrage du polling
        await dp.start_polling(bot)
        
    except Exception as e:
        logger.error(f"❌ Erreur lors du démarrage: {e}")
    finally:
        # Nettoyage
        await shutdown_community_manager()
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
