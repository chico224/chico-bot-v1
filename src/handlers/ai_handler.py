"""
Handler IA principal - Toutes les réponses du bot utilisent l'IA

Fonctionnement :
- Intercepte TOUS les messages utilisateurs
- Génère des réponses avec OpenAI GPT-4o + Gemini 1.5-flash
- Ton guinéen fraternel et ultra-émotionnel
- Réponses dynamiques et uniques
- Fallback automatique en cas d'erreur

🇬🇳 La Guinée se soulève avec l'intelligence artificielle ! 🇬🇳
"""

import asyncio
import logging
from typing import Dict, Optional

from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from core.ai_response import generate_ai_response
from core.database import database
from core.logging_setup import get_logger

# Configuration du logger
logger = get_logger(__name__)

# Router principal pour les messages IA
ai_router = Router()

# Commandes qui ne doivent PAS utiliser l'IA (déjà gérées spécifiquement)
EXCLUDED_COMMANDS = {
    "/start",
    "/classement", 
    "/support",
    "/bounties",
    "/palier",
    "/withdraw",
    "/trading",
    "/invest",
    "/stats",
    "/help"
}

@ai_router.message()
async def handle_general_messages(message: types.Message):
    """
    Handler principal pour TOUS les messages utilisateurs.
    Génère des réponses IA avec ton guinéen fraternel.
    """
    try:
        user_id = message.from_user.id
        username = message.from_user.username or "ami"
        message_text = message.text or message.caption or ""
        
        logger.info(f"🇬🇳 Message de @{username}: {message_text[:50]}...")
        
        # Ignorer les commandes déjà gérées spécifiquement
        if message_text.startswith('/') and message_text.split()[0] in EXCLUDED_COMMANDS:
            return
        
        # Récupérer les infos utilisateur pour personnalisation
        user_info = await get_user_info_for_ai(user_id, username)
        
        # Déterminer le contexte en fonction du message
        context = determine_message_context(message_text)
        
        # Générer la réponse IA avec ton guinéen
        ai_response = await generate_ai_response(
            user_id=user_id,
            message=message_text,
            context=context,
            user_info=user_info
        )
        
        # Envoyer la réponse IA
        await message.answer(ai_response.content, parse_mode="Markdown")
        
        logger.info(f"🇬🇳 Réponse IA envoyée à @{username} ({ai_response.model_used})")
        
    except Exception as e:
        logger.error(f"🇬🇳 Erreur handler message général: {e}")
        
        # Réponse IA d'erreur
        try:
            error_response = await generate_ai_response(
                user_id=message.from_user.id,
                message=message_text,
                context="error"
            )
            await message.answer(error_response.content, parse_mode="Markdown")
        except:
            # Fallback ultime
            await message.answer(
                "🇬🇳 Frère/sœur, j'ai un petit problème technique ❤️\n\n"
                "🔄 Donne-moi une seconde et je reviens mieux que jamais !\n\n"
                "🚀 La famille ChicoBot est toujours là pour toi 🔥🇬🇳"
            )

@ai_router.callback_query()
async def handle_general_callbacks(callback: CallbackQuery):
    """
    Handler principal pour TOUS les callbacks non gérés spécifiquement.
    Génère des réponses IA avec ton guinéen fraternel.
    """
    try:
        user_id = callback.from_user.id
        username = callback.from_user.username or "ami"
        callback_data = callback.data
        
        logger.info(f"🇬🇳 Callback de @{username}: {callback_data}")
        
        # Callbacks déjà gérés spécifiquement - ignorer
        excluded_callbacks = {
            "send_wallet",
            "refresh_ranking",
            "my_stats",
            "concours_info", 
            "support_info",
            "contact_chico",
            "contact_problematique",
            "tech_support",
            "general_support",
            "flag_",
            "fire",
            "trophy",
            "money",
            "celebrate",
            "crown",
            "lightning",
            "diamond"
        }
        
        if any(callback_data.startswith(excluded) for excluded in excluded_callbacks):
            return
        
        # Récupérer les infos utilisateur
        user_info = await get_user_info_for_ai(user_id, username)
        
        # Déterminer le contexte
        context = determine_callback_context(callback_data)
        
        # Générer la réponse IA
        ai_response = await generate_ai_response(
            user_id=user_id,
            message=f"Callback: {callback_data}",
            context=context,
            user_info=user_info
        )
        
        # Répondre au callback
        await callback.message.answer(ai_response.content, parse_mode="Markdown")
        await callback.answer()
        
        logger.info(f"🇬🇳 Réponse IA callback envoyée à @{username}")
        
    except Exception as e:
        logger.error(f"🇬🇳 Erreur handler callback général: {e}")
        
        # Réponse IA d'erreur
        try:
            error_response = await generate_ai_response(
                user_id=callback.from_user.id,
                message=f"Callback: {callback.data}",
                context="error"
            )
            await callback.message.answer(error_response.content, parse_mode="Markdown")
            await callback.answer()
        except:
            # Fallback ultime
            await callback.answer("⚠️ Erreur technique", show_alert=True)
            await callback.message.answer(
                "🇬🇳 Frère/sœur, j'ai un petit problème technique ❤️\n\n"
                "🔄 Réessaie dans quelques instants !\n\n"
                "🚀 La famille ChicoBot t'attend ! 🔥🇬🇳"
            )

async def get_user_info_for_ai(user_id: int, username: str) -> Dict:
    """
    Récupère les informations utilisateur pour personnaliser les réponses IA.
    """
    try:
        # Récupérer les stats utilisateur depuis la base de données
        user_stats = await database.get_user_stats(user_id)
        
        if user_stats:
            return {
                "username": username,
                "total_earnings": user_stats.get("total_earnings", 0),
                "global_rank": user_stats.get("global_rank"),
                "guinea_rank": user_stats.get("guinea_rank"),
                "monthly_earnings": user_stats.get("monthly_earnings", 0),
                "country": "GN",  # Par défaut Guinée
                "next_milestone": user_stats.get("next_milestone", 500)
            }
        else:
            # Utilisateur par défaut
            return {
                "username": username,
                "total_earnings": 0,
                "global_rank": None,
                "guinea_rank": None,
                "monthly_earnings": 0,
                "country": "GN",
                "next_milestone": 500
            }
            
    except Exception as e:
        logger.error(f"🇬🇳 Erreur récupération infos utilisateur: {e}")
        
        # Retourner les infos par défaut
        return {
            "username": username,
            "total_earnings": 0,
            "global_rank": None,
            "guinea_rank": None,
            "monthly_earnings": 0,
            "country": "GN",
            "next_milestone": 500
        }

def determine_message_context(message_text: str) -> str:
    """
    Détermine le contexte du message pour l'IA.
    """
    message_lower = message_text.lower()
    
    # Contextes spécifiques selon le contenu
    if any(word in message_lower for word in ["trading", "trade", "xauusd", "or", "marché"]):
        return "trading"
    elif any(word in message_lower for word in ["bounty", "bounties", "tâche", "task", "job"]):
        return "bounty"
    elif any(word in message_lower for word in ["invest", "investissement", "portfolio", "rendement"]):
        return "investment"
    elif any(word in message_lower for word in ["concours", "compétition", "gagner", "prix"]):
        return "concours"
    elif any(word in message_lower for word in ["aide", "help", "support", "problème", "erreur"]):
        return "support"
    elif any(word in message_lower for word in ["classement", "top", "rang", "meilleur"]):
        return "classement"
    elif any(word in message_lower for word in ["salut", "bonjour", "yo", "wsh", "cc"]):
        return "greeting"
    elif any(word in message_lower for word in ["merci", "thank", "cool", "génial", "super"]):
        return "gratitude"
    elif any(word in message_lower for word in ["chico", "oumar", "sow", "problematique", "ibrahima", "barry"]):
        return "creators"
    elif any(word in message_lower for word in ["kamsar", "conakry", "guinée", "guinea"]):
        return "guinea"
    elif any(word in message_lower for word in ["argent", "money", "gains", "revenus", "richesse"]):
        return "money"
    elif any(word in message_lower for word in ["comment", "comment marche", "comment faire", "how to"]):
        return "tutorial"
    elif any(word in message_lower for word in ["pourquoi", "why", "raison"]):
        return "explanation"
    elif any(word in message_lower for word in ["qui", "who", "quel", "quelle"]):
        return "information"
    else:
        return "general"

def determine_callback_context(callback_data: str) -> str:
    """
    Détermine le contexte du callback pour l'IA.
    """
    callback_lower = callback_data.lower()
    
    if "trading" in callback_lower:
        return "trading"
    elif "bounty" in callback_lower:
        return "bounty"
    elif "invest" in callback_lower:
        return "investment"
    elif "concours" in callback_lower:
        return "concours"
    elif "support" in callback_lower:
        return "support"
    elif "classement" in callback_lower:
        return "classement"
    elif "stats" in callback_lower:
        return "stats"
    elif "wallet" in callback_lower:
        return "wallet"
    elif "withdraw" in callback_lower:
        return "withdraw"
    elif "palier" in callback_lower:
        return "palier"
    else:
        return "general"

# Handlers pour les commandes restantes avec IA

@ai_router.message(Command("trading"))
async def handle_trading_command(message: types.Message):
    """Gère la commande /trading avec IA."""
    try:
        user_id = message.from_user.id
        username = message.from_user.username or "ami"
        
        # Récupérer les infos utilisateur
        user_info = await get_user_info_for_ai(user_id, username)
        
        # Générer la réponse IA spécialisée trading
        ai_response = await generate_ai_response(
            user_id=user_id,
            message="/trading",
            context="trading",
            user_info=user_info
        )
        
        await message.answer(ai_response.content, parse_mode="Markdown")
        
        logger.info(f"🇬🇳 Commande /trading pour @{username}")
        
    except Exception as e:
        logger.error(f"🇬🇳 Erreur commande /trading: {e}")
        
        error_response = await generate_ai_response(
            user_id=message.from_user.id,
            message="/trading",
            context="error"
        )
        
        await message.answer(error_response.content, parse_mode="Markdown")

@ai_router.message(Command("invest"))
async def handle_invest_command(message: types.Message):
    """Gère la commande /invest avec IA."""
    try:
        user_id = message.from_user.id
        username = message.from_user.username or "ami"
        
        # Récupérer les infos utilisateur
        user_info = await get_user_info_for_ai(user_id, username)
        
        # Générer la réponse IA spécialisée investissement
        ai_response = await generate_ai_response(
            user_id=user_id,
            message="/invest",
            context="investment",
            user_info=user_info
        )
        
        await message.answer(ai_response.content, parse_mode="Markdown")
        
        logger.info(f"🇬🇳 Commande /invest pour @{username}")
        
    except Exception as e:
        logger.error(f"🇬🇳 Erreur commande /invest: {e}")
        
        error_response = await generate_ai_response(
            user_id=message.from_user.id,
            message="/invest",
            context="error"
        )
        
        await message.answer(error_response.content, parse_mode="Markdown")

@ai_router.message(Command("stats"))
async def handle_stats_command(message: types.Message):
    """Gère la commande /stats avec IA."""
    try:
        user_id = message.from_user.id
        username = message.from_user.username or "ami"
        
        # Récupérer les infos utilisateur
        user_info = await get_user_info_for_ai(user_id, username)
        
        # Générer la réponse IA spécialisée stats
        ai_response = await generate_ai_response(
            user_id=user_id,
            message="/stats",
            context="stats",
            user_info=user_info
        )
        
        await message.answer(ai_response.content, parse_mode="Markdown")
        
        logger.info(f"🇬🇳 Commande /stats pour @{username}")
        
    except Exception as e:
        logger.error(f"🇬🇳 Erreur commande /stats: {e}")
        
        error_response = await generate_ai_response(
            user_id=message.from_user.id,
            message="/stats",
            context="error"
        )
        
        await message.answer(error_response.content, parse_mode="Markdown")

@ai_router.message(Command("help"))
async def handle_help_command(message: types.Message):
    """Gère la commande /help avec IA."""
    try:
        user_id = message.from_user.id
        username = message.from_user.username or "ami"
        
        # Récupérer les infos utilisateur
        user_info = await get_user_info_for_ai(user_id, username)
        
        # Générer la réponse IA spécialisée aide
        ai_response = await generate_ai_response(
            user_id=user_id,
            message="/help",
            context="help",
            user_info=user_info
        )
        
        await message.answer(ai_response.content, parse_mode="Markdown")
        
        logger.info(f"🇬🇳 Commande /help pour @{username}")
        
    except Exception as e:
        logger.error(f"🇬🇳 Erreur commande /help: {e}")
        
        error_response = await generate_ai_response(
            user_id=message.from_user.id,
            message="/help",
            context="error"
        )
        
        await message.answer(error_response.content, parse_mode="Markdown")

# Fonctions utilitaires

async def register_ai_handlers(dispatcher):
    """
    Enregistre tous les handlers IA dans le dispatcher.
    """
    dispatcher.include_router(ai_router)
    logger.info("🇬🇳 Handlers IA enregistrés avec succès")

# Tests d'intégration
if __name__ == "__main__":
    import unittest
    from unittest import IsolatedAsyncioTestCase
    
    class TestAIHandler(IsolatedAsyncioTestCase):
        """Tests pour le handler IA."""
        
        async def test_context_determination(self):
            """Teste la détermination automatique de contexte."""
            
            # Tests de contexte trading
            self.assertEqual(determine_message_context("comment marche le trading"), "trading")
            self.assertEqual(determine_message_context("XAUUSD"), "trading")
            self.assertEqual(determine_message_context("l'or monte"), "trading")
            
            # Tests de contexte bounty
            self.assertEqual(determine_message_context("je veux des bounties"), "bounty")
            self.assertEqual(determine_message_context("tâches disponibles"), "bounty")
            
            # Tests de contexte support
            self.assertEqual(determine_message_context("j'ai besoin d'aide"), "support")
            self.assertEqual(determine_message_context("problème technique"), "support")
            
            # Tests de contexte général
            self.assertEqual(determine_message_context("salut comment ça va"), "greeting")
            self.assertEqual(determine_message_context("message random"), "general")
            
            print("\n🎯 Détermination de contexte fonctionne correctement")
        
        async def test_callback_context(self):
            """Teste la détermination de contexte pour callbacks."""
            
            self.assertEqual(determine_callback_context("trading_info"), "trading")
            self.assertEqual(determine_callback_context("bounty_list"), "bounty")
            self.assertEqual(determine_callback_context("random_callback"), "general")
            
            print("\n🎯 Détermination contexte callbacks fonctionne")
        
        async def test_user_info_retrieval(self):
            """Teste la récupération des infos utilisateur."""
            
            # Test avec utilisateur existant (simulation)
            user_info = await get_user_info_for_ai(123456, "test_user")
            
            self.assertIn("username", user_info)
            self.assertIn("total_earnings", user_info)
            self.assertIn("country", user_info)
            self.assertEqual(user_info["country"], "GN")
            
            print("\n👤 Récupération infos utilisateur fonctionne")
    
    # Lancer les tests
    unittest.main(verbosity=2)
