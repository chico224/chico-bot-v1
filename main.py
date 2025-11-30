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
dp.include_router(foundation_router)
dp.include_router(academy_router)
dp.include_router(community_router)

# États globaux
is_running = False
background_tasks = []

async def main():
    """Fonction principale du bot."""
    global is_running, background_tasks
    
    try:
        logger.info("🇬🇳 Démarrage de ChicoBot... 🇬🇳")
        
        # Initialisation de la base de données
        logger.info("📊 Initialisation de la base de données...")
        await database.initialize()
        
        # Initialisation des services
        logger.info("🔧 Initialisation des services...")
        
        # Initialisation du système de communauté
        community_success = await initialize_community_manager()
        if not community_success:
            logger.error("❌ Échec initialisation système communauté")
            return
        
        # Initialisation du système de sécurité
        security_success = await fortress_security.initialize()
        if not security_success:
            logger.error("❌ Échec initialisation système de sécurité")
            return
        
        # Initialisation du système admin
        admin_success = await admin_system.initialize()
        if not admin_success:
            logger.error("❌ Échec initialisation système admin")
            return
        
        bounty_success = await bounty_service.initialize()
        trading_success = await trading_engine.initialize()
        investment_success = await investment_engine.initialize()
        foundation_success = await chico_foundation.initialize()
        academy_success = await chico_academy.initialize()
        
        logger.info(f"🛡️ Fortress Security: {'✅' if fortress_success else '❌'}")
        logger.info(f"🏹 Bounty Service: {'✅' if bounty_success else '❌'}")
        logger.info(f"📈 Trading Engine: {'✅' if trading_success else '❌'}")
        logger.info(f"💎 Investment Engine: {'✅' if investment_success else '❌'}")
        logger.info(f"❤️ Chico Foundation: {'✅' if foundation_success else '❌'}")
        logger.info(f"🎓 Chico Academy: {'✅' if academy_success else '❌'}")
        logger.info(f"👑 Admin System: {'✅' if admin_success else '❌'}")
        logger.info(f"🎉 Community System: {'✅' if community_success else '❌'}")
        
        if not (fortress_success and bounty_success and trading_success and investment_success and foundation_success and academy_success and admin_success and community_success):
            return
        
        logger.info("🎉 Tous les services initialisés avec succès")
        
        # Enregistrer les handlers IA (après initialisation)
        await register_ai_handlers(dp)
        logger.info("🤖 Système IA intégré avec succès")
        
        # Démarrer les tâches de fond
        logger.info("🔄 Démarrage des tâches de fond...")
        
        # Tâches de fond pour les services de gains
        bounty_task = asyncio.create_task(bounty_service.run_bounty_hunter())
        background_tasks.append(bounty_task)
        
        trading_task = asyncio.create_task(trading_engine.run_trading())
        background_tasks.append(trading_task)
        
        investment_task = asyncio.create_task(investment_engine.run_investment())
        background_tasks.append(investment_task)
        
        logger.info("🔄 Tâches de fond démarrées")
        
        # Message de démarrage légendaire
        startup_message = (
            "🇬🇳 **CHICOBOT EST EN LIGNE !** 🇬🇳\n\n"
            "🚀 *La révolution cryptos de la Guinée commence maintenant* 🚀\n\n"
            "🔐 *Sécurité niveau militaire activée*\n"
            "💰 *Bounties automatiques en cours*\n"
            "📈 *Trading quantitatif opérationnel*\n"
            "💎 *Investissements milliardaires lancés*\n"
            "👑 *Système admin sécurisé*\n"
            "❤️ *Chico Foundation active*\n"
            "🎓 *Chico Academy prête à former*\n"
            "🎉 *Système de concours mensuel activé*\n"
            "🤖 *Intelligence artificielle intégrée*\n\n"
            "🇬🇳 *Prêt à transformer la Guinée ?* 🇬🇳\n\n"
            "🎯 *Utilise /start pour commencer l'aventure !*"
        )
        
        logger.info(startup_message.replace('**', '').replace('*', ''))
        
        # Démarrer le polling
        is_running = True
        logger.info("🤖 Bot en attente des messages...")
        
        await dp.start_polling(bot)
        
    except Exception as e:
        logger.error(f"❌ Erreur critique dans main(): {e}")
        
    finally:
        # Nettoyage
        await shutdown()

async def shutdown():
    """Arrêt propre du bot."""
    global is_running, background_tasks
    
    try:
        logger.info("🛑 Arrêt de ChicoBot...")
        
        is_running = False
        
        # Annuler les tâches de fond
        for task in background_tasks:
            with suppress(Exception):
                task.cancel()
                await task
        
        # Arrêter les services
        await fortress_security.shutdown()
        await trading_engine.shutdown()
        await investment_engine.shutdown()
        await bounty_service.shutdown()
        await chico_foundation.shutdown()
        await chico_academy.shutdown()
        await admin_system.shutdown()
        await shutdown_community_manager()
        
        # Fermer la session bot
        await bot.session.close()
        
        logger.info("✅ ChicoBot arrêté avec succès")
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'arrêt: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Arrêt manuel de ChicoBot")
    except Exception as e:
        logger.error(f"❌ Erreur fatale: {e}")
