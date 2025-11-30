"""
ChicoBot Principal - Le bot avec la voix de Chico
TOUTES les réponses passent par le moteur de personnalité Chico
17 ans, Kamsar, Guinée - cœur immense, voix qui donne des frissons
"""

import asyncio
import logging
import os
from datetime import datetime
from typing import Dict, Any

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

# Imports Chico
from src.core.chico_personality import get_chico_engine, chico_respond
from src.core.database import DatabaseManager
from src.core.multitask_integration import start_multitask_system, check_balance_and_unlock
from src.handlers.chico_handlers import get_chico_handlers
from src.core.logging_setup import setup_logging

logger = setup_logging("main_bot_chico")

class ChicoBot:
    """
    ChicoBot - Le bot avec la voix de Chico
    17 ans, Kamsar, Guinée - cœur immense
    TOUTES les réponses passent par le moteur IA
    """
    
    def __init__(self):
        # Configuration
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not self.bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN non trouvé dans les variables d'environnement")
            
        # Initialisation bot
        self.bot = Bot(token=self.bot_token)
        self.dp = Dispatcher()
        
        # Composants Chico
        self.database = DatabaseManager()
        self.chico_engine = get_chico_engine(self.database)
        self.handlers = get_chico_handlers()
        
        # Système multitâche
        self.orchestrator = None
        
        # Statistiques
        self.start_time = datetime.now()
        self.messages_processed = 0
        
        logger.info("🇬🇳 ChicoBot initialisé - Mode Personality activé")
        
    async def initialize(self):
        """Initialisation complète du bot"""
        
        # Initialiser le moteur Chico
        await self.chico_engine.initialize()
        
        # Démarrer le système multitâche
        try:
            self.orchestrator = await start_multitask_system(self.database)
            logger.info("🚀 Système multitâche démarré")
        except Exception as e:
            logger.warning(f"Système multitâche indisponible: {e}")
            
        # Enregistrer les handlers
        await self._register_handlers()
        
        logger.info("✅ ChicoBot prêt à parler avec son cœur !")
        
    async def _register_handlers(self):
        """Enregistrement de TOUS les handlers - TOUT passe par Chico"""
        
        # Commandes de base
        @self.dp.message(Command("start"))
        async def cmd_start(message: Message):
            await self._handle_with_chico("start", message)
            
        @self.dp.message(Command("help"))
        async def cmd_help(message: Message):
            await self._handle_with_chico("help", message)
            
        @self.dp.message(Command("balance"))
        async def cmd_balance(message: Message):
            await self._handle_with_chico("balance", message)
            
        @self.dp.message(Command("deposit"))
        async def cmd_deposit(message: Message):
            await self._handle_with_chico("deposit", message)
            
        @self.dp.message(Command("trading"))
        async def cmd_trading(message: Message):
            await self._handle_with_chico("trading", message)
            
        @self.dp.message(Command("withdraw"))
        async def cmd_withdraw(message: Message):
            await self._handle_with_chico("withdraw", message)
            
        @self.dp.message(Command("stats"))
        async def cmd_stats(message: Message):
            await self._handle_with_chico("stats", message)
            
        @self.dp.message(Command("classement"))
        async def cmd_classement(message: Message):
            await self._handle_with_chico("classement", message)
            
        @self.dp.message(Command("support"))
        async def cmd_support(message: Message):
            await self._handle_with_chico("support", message)
            
        @self.dp.message(Command("tasks"))
        async def cmd_tasks(message: Message):
            await self._handle_with_chico("multitask_status", message)
            
        # Messages généraux - TOUS passent par Chico
        @self.dp.message()
        async def handle_general(message: Message):
            await self._handle_with_chico("general", message)
            
        logger.info("📞 Handlers enregistrés - TOUT passe par la voix de Chico")
        
    async def _handle_with_chico(self, handler_type: str, message: Message):
        """
        Handler universel - TOUTES les réponses passent par Chico
        """
        
        try:
            user_id = str(message.from_user.id)
            username = message.from_user.username
            
            # Statistiques
            self.messages_processed += 1
            
            # Log du message original
            logger.info(f"📩 Message {handler_type} de {username} ({user_id}): {message.text}")
            
            # Traitement selon le type
            if handler_type == "start":
                response = await self.handlers.handle_start(user_id, username)
            elif handler_type == "help":
                response = await self.handlers.handle_help(user_id)
            elif handler_type == "balance":
                response = await self.handlers.handle_balance(user_id)
            elif handler_type == "deposit":
                # Extraire le montant si spécifié
                amount = self._extract_amount(message.text)
                response = await self.handlers.handle_deposit(user_id, amount)
            elif handler_type == "trading":
                # Extraire l'action si spécifiée
                action = self._extract_trading_action(message.text)
                response = await self.handlers.handle_trading(user_id, action)
            elif handler_type == "withdraw":
                # Extraire le montant si spécifié
                amount = self._extract_amount(message.text)
                response = await self.handlers.handle_withdraw(user_id, amount)
            elif handler_type == "stats":
                response = await self.handlers.handle_stats(user_id)
            elif handler_type == "classement":
                response = await self.handlers.handle_classement(user_id)
            elif handler_type == "support":
                # Extraire le message de support
                support_msg = self._extract_support_message(message.text)
                response = await self.handlers.handle_support(user_id, support_msg)
            elif handler_type == "multitask_status":
                response = await self.handlers.handle_multitask_status(user_id)
            elif handler_type == "general":
                # Message général - passe directement par Chico
                response = await self.handlers.handle_general_message(user_id, message.text)
            else:
                # Fallback
                response = await chico_respond(message.text, user_id)
                
            # Envoyer la réponse
            await message.answer(response)
            
            # Si c'était une transaction, vérifier les paliers
            if handler_type in ["deposit"] and self.orchestrator:
                balance = await self.database.get_user_balance(user_id)
                await check_balance_and_unlock(self.database, balance)
                
            # Log de la réponse
            logger.info(f"📤 Réponse Chico envoyée à {username}: {len(response)} caractères")
            
        except Exception as e:
            logger.error(f"Erreur handler {handler_type}: {e}")
            
            # Message d'erreur avec la voix de Chico
            error_response = await chico_respond(
                "Désolé frère, j'ai eu un petit problème... Réessaie dans un instant !",
                user_id
            )
            await message.answer(error_response)
            
    def _extract_amount(self, text: str) -> float:
        """Extraire un montant d'un message"""
        import re
        
        # Chercher des nombres dans le texte
        numbers = re.findall(r'\d+\.?\d*', text)
        if numbers:
            try:
                return float(numbers[0])
            except:
                pass
        return None
        
    def _extract_trading_action(self, text: str) -> str:
        """Extraire l'action de trading"""
        text_lower = text.lower()
        
        if "start" in text_lower or "lancer" in text_lower or "commencer" in text_lower:
            return "start"
        elif "stop" in text_lower or "arrêter" in text_lower or "pause" in text_lower:
            return "stop"
        else:
            return "status"
            
    def _extract_support_message(self, text: str) -> str:
        """Extraire le message de support"""
        # Enlever "/support" du début
        if text.startswith("/support"):
            return text[9:].strip()
        return None
        
    async def start_bot(self):
        """Démarrage du bot"""
        
        logger.info("🚀 Démarrage de ChicoBot - La voix de Kamsar !")
        
        # Message de démarrage
        print("🇬🇳 CHICOBOT - DÉMARRAGE")
        print("="*50)
        print("🔥 Mode Personality activé")
        print("💬 Toutes les réponses passent par Chico (17 ans, Kamsar)")
        print("🤖 IA: OpenAI GPT-4o + Gemini 1.5-flash")
        print("📊 Système multitâche: Actif")
        print("🇬🇳 La Guinée se soulève !")
        print("="*50)
        
        # Démarrer le polling
        await self.dp.start_polling(
            self.bot,
            skip_updates=True
        )
        
    async def stop_bot(self):
        """Arrêt propre du bot"""
        
        logger.info("🛑 Arrêt de ChicoBot")
        
        # Arrêter le système multitâche
        if self.orchestrator:
            await self.orchestrator.stop_all_tasks()
            
        # Nettoyer le moteur Chico
        await self.chico_engine.cleanup()
        
        # Arrêter le bot
        await self.bot.session.close()
        
        logger.info("🇬🇳 ChicoBot arrêté - À bientôt la famille !")

# Point d'entrée principal
async def main():
    """Point d'entrée principal"""
    
    # Vérifier les variables d'environnement
    required_vars = ["TELEGRAM_BOT_TOKEN", "OPENAI_PROJECT_API_KEY", "GEMINI_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print("❌ Variables d'environnement manquantes:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\n📖 Ajoutez-les dans votre fichier .env")
        return
        
    # Créer et démarrer le bot
    bot = ChicoBot()
    
    try:
        await bot.initialize()
        await bot.start_bot()
    except KeyboardInterrupt:
        print("\n🛑 Arrêt demandé par l'utilisateur")
    except Exception as e:
        logger.error(f"Erreur fatale: {e}")
    finally:
        await bot.stop_bot()

# Démarrage
if __name__ == "__main__":
    asyncio.run(main())
