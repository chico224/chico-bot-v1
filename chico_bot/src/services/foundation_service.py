"""
Chico Foundation Service - Système de Charité Automatique.

Fonctionnalités principales :
- Prélèvement automatique de 1% sur tous les gains (bounty, trading, investissement)
- Messages émotionnels à chaque reversement
- Tracking complet des donations
- Compteur global des fonds récoltés
- Intégration transparente avec les services de gains

🇬🇳❤️ La Guinée se soulève ensemble 🇬🇳❤️
"""

import asyncio
import hashlib
import json
import logging
import random
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from aiogram import Router, types
from aiogram.enums import ParseMode
from aiogram.filters import Command

from config.settings import settings
from core.database import database
from core.logging_setup import get_logger

# Configuration du logger
logger = get_logger(__name__)

# Router pour les commandes foundation
foundation_router = Router()

# 🇬🇳 Configuration Chico Foundation 🇬🇳
FOUNDATION_RATE = 0.01  # 1% des gains
FOUNDATION_MESSAGE_COOLDOWN = 86400  # 24 heures entre les messages pour un même utilisateur
FOUNDATION_WALLET = "chico_foundation_treasury"  # Portefeuille foundation

# 🇬🇳 Message de la Chico Foundation 🇬🇳
FOUNDATION_MESSAGE = """
❤️ *1 % de ton gain vient d’être reversé à la Chico Foundation* ❤️

Grâce à toi, aujourd’hui :
- Des enfants de Kamsar et Conakry ont reçu des cahiers, stylos et uniformes  
- Des mamans seules ont eu de la nourriture pour leurs bébés  
- Des jeunes filles ont eu des serviettes hygiéniques pour aller à l’école sans honte  
- Des orphelins ont eu un toit et un repas chaud  

Ce 1 % n’est pas une taxe.  
C’est la preuve que la Guinée se soulève ensemble.

Chico & Problematique te remercient du fond du cœur.  
Tu ne changes pas seulement ta vie.  
Tu changes la Guinée.  
Une transaction à la fois.

🇬🇳❤️ Merci frère/sœur. Tu es la Chico Family. ❤️🇬🇳
"""

# 🇬🇳 Messages d'impact spécifiques 🇬🇳
IMPACT_MESSAGES = [
    "📚 *Aujourd'hui, 10 enfants de Kamsar ont des cahiers neufs grâce à toi* 📚",
    "🍼 *Grâce à ton 1%, une maman seule a pu nourrir son bébé pour une semaine* 🍼",
    "👧 *Une jeune fille peut aller à l'école avec dignité grâce à tes serviettes hygiéniques* 👧",
    "🏠 *Un orphelin a un toit et un repas chaud ce soir grâce à ta générosité* 🏠",
    "🎒 *Un élève a un uniforme neuf et est fier d'aller à l'école grâce à toi* 🎒",
    "🥄 *Une famille a mangé à sa faim aujourd'hui grâce à ta contribution* 🥄",
    "💊 *Un enfant malade a reçu ses médicaments grâce à ton 1%* 💊",
    "🌟 *Un jeune talent a pu suivre une formation grâce à ton soutien* 🌟"
]

class ChicoFoundation:
    """Système de gestion de la Chico Foundation."""
    
    def __init__(self):
        self.total_collected = 0.0
        self.monthly_collected = 0.0
        self.daily_collected = 0.0
        self.user_last_message = {}  # Pour éviter le spam
        self.donation_history = []
        self.impact_stats = {
            "children_helped": 0,
            "meals_provided": 0,
            "school_supplies": 0,
            "families_supported": 0,
            "orphans_housed": 0
        }
        self.is_initialized = False
        
    async def initialize(self) -> bool:
        """Initialise le service foundation."""
        try:
            logger.info("🇬🇳 Initialisation de la Chico Foundation... 🇬🇳")
            
            # Charger les données depuis la base de données
            await self._load_foundation_data()
            
            # Démarrer les tâches de fond
            asyncio.create_task(self._daily_reset())
            asyncio.create_task(self._monthly_reset())
            asyncio.create_task(self._impact_calculator())
            
            self.is_initialized = True
            
            logger.info(f"🇬🇳 Chico Foundation initialisée - Total récolté : {self.total_collected:.2f}$ 🇬🇳")
            
            return True
            
        except Exception as e:
            logger.error(f"🇬🇳 Erreur initialisation foundation: {e}")
            return False
    
    async def _load_foundation_data(self):
        """Charge les données de la foundation depuis la base de données."""
        try:
            # Récupérer les statistiques globales
            foundation_stats = await database.get_foundation_stats()
            
            if foundation_stats:
                self.total_collected = foundation_stats.get("total_collected", 0.0)
                self.monthly_collected = foundation_stats.get("monthly_collected", 0.0)
                self.daily_collected = foundation_stats.get("daily_collected", 0.0)
                self.impact_stats = foundation_stats.get("impact_stats", self.impact_stats)
            
            # Récupérer l'historique des donations récentes
            recent_donations = await database.get_recent_foundation_donations(100)
            self.donation_history = recent_donations
            
            # Récupérer les timestamps des derniers messages
            user_messages = await database.get_user_foundation_messages()
            self.user_last_message = {msg["user_id"]: msg["last_message_time"] for msg in user_messages}
            
            logger.info(f"🇬🇳 Données foundation chargées - {len(self.donation_history)} donations")
            
        except Exception as e:
            logger.error(f"🇬🇳 Erreur chargement données foundation: {e}")
    
    async def process_gain(self, user_id: int, username: str, gain_amount: float, gain_type: str) -> Dict[str, Any]:
        """Traite un gain et prélève 1% pour la foundation."""
        try:
            if not self.is_initialized:
                logger.warning("🇬🇳 Foundation non initialisée - traitement ignoré")
                return {"success": False, "message": "Foundation non disponible"}
            
            if gain_amount <= 0:
                return {"success": False, "message": "Gain invalide"}
            
            # Calculer le prélèvement (1%)
            foundation_amount = gain_amount * FOUNDATION_RATE
            user_net_amount = gain_amount - foundation_amount
            
            # Enregistrer la donation
            donation_data = {
                "user_id": user_id,
                "username": username,
                "original_gain": gain_amount,
                "foundation_amount": foundation_amount,
                "user_net_amount": user_net_amount,
                "gain_type": gain_type,  # "bounty", "trading", "investment"
                "timestamp": datetime.now()
            }
            
            # Sauvegarder en base de données
            await database.add_foundation_donation(donation_data)
            
            # Mettre à jour les compteurs
            await self._update_counters(foundation_amount)
            
            # Ajouter à l'historique
            self.donation_history.append(donation_data)
            
            # Limiter l'historique
            if len(self.donation_history) > 1000:
                self.donation_history = self.donation_history[-1000:]
            
            # Calculer l'impact
            await self._calculate_impact(foundation_amount)
            
            # Envoyer le message à l'utilisateur (si cooldown respecté)
            should_send_message = await self._should_send_message(user_id)
            
            if should_send_message:
                await self._send_foundation_message(user_id, foundation_amount, gain_type)
            
            logger.info(f"🇬🇳 Foundation: {username} ({user_id}) - {foundation_amount:.2f}$ prélevés sur {gain_amount:.2f}$ ({gain_type})")
            
            return {
                "success": True,
                "original_gain": gain_amount,
                "foundation_amount": foundation_amount,
                "user_net_amount": user_net_amount,
                "message_sent": should_send_message,
                "gain_type": gain_type
            }
            
        except Exception as e:
            logger.error(f"🇬🇳 Erreur traitement gain foundation: {e}")
            return {"success": False, "message": "Erreur technique"}
    
    async def _update_counters(self, amount: float):
        """Met à jour les compteurs de la foundation."""
        try:
            self.total_collected += amount
            self.monthly_collected += amount
            self.daily_collected += amount
            
            # Sauvegarder en base de données
            await database.update_foundation_stats({
                "total_collected": self.total_collected,
                "monthly_collected": self.monthly_collected,
                "daily_collected": self.daily_collected,
                "impact_stats": self.impact_stats,
                "last_updated": datetime.now()
            })
            
        except Exception as e:
            logger.error(f"🇬🇳 Erreur mise à jour compteurs: {e}")
    
    async def _calculate_impact(self, amount: float):
        """Calcule l'impact réel des donations."""
        try:
            # Estimations basées sur les coûts réels en Guinée
            # 1$ = 1 enfant aidé (cahiers + stylos)
            # 0.5$ = 1 repas pour un enfant
            # 2$ = 1 uniforme scolaire
            # 5$ = 1 semaine de nourriture pour une famille
            # 10$ = 1 mois de soutien pour un orphelin
            
            children_helped = int(amount * 1.0)
            meals_provided = int(amount * 2.0)
            school_supplies = int(amount * 0.5)
            families_supported = int(amount * 0.2)
            orphans_housed = int(amount * 0.1)
            
            self.impact_stats["children_helped"] += children_helped
            self.impact_stats["meals_provided"] += meals_provided
            self.impact_stats["school_supplies"] += school_supplies
            self.impact_stats["families_supported"] += families_supported
            self.impact_stats["orphans_housed"] += orphans_housed
            
        except Exception as e:
            logger.error(f"🇬🇳 Erreur calcul impact: {e}")
    
    async def _should_send_message(self, user_id: int) -> bool:
        """Vérifie si on doit envoyer un message à l'utilisateur."""
        try:
            current_time = datetime.now()
            
            # Vérifier le cooldown (24 heures)
            if user_id in self.user_last_message:
                last_message_time = self.user_last_message[user_id]
                time_diff = current_time - last_message_time
                
                if time_diff < timedelta(seconds=FOUNDATION_MESSAGE_COOLDOWN):
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"🇬🇳 Erreur vérification message: {e}")
            return False
    
    async def _send_foundation_message(self, user_id: int, amount: float, gain_type: str):
        """Envoie le message foundation à l'utilisateur."""
        try:
            # Sélectionner un message d'impact aléatoire
            impact_message = random.choice(IMPACT_MESSAGES)
            
            # Message personnalisé selon le type de gain
            type_emoji = {
                "bounty": "💰",
                "trading": "📈", 
                "investment": "💎"
            }.get(gain_type, "💵")
            
            personalized_message = (
                f"{type_emoji} *Ton gain de {gain_type}* {type_emoji}\n\n"
                f"{FOUNDATION_MESSAGE}\n\n"
                f"{impact_message}\n\n"
                f"💝 *Montant reversé :* {amount:.2f}$\n"
                f"🇬🇳 *Total foundation :* {self.total_collected:.2f}$ 🇬🇳"
            )
            
            # Envoyer le message (via le bot)
            # Note: Cette fonction nécessiterait l'accès au bot instance
            # Pour l'instant, on loggue le message
            logger.info(f"🇬🇳 Message foundation pour utilisateur {user_id}: {amount:.2f}$")
            
            # Mettre à jour le timestamp du dernier message
            self.user_last_message[user_id] = datetime.now()
            await database.update_user_foundation_message(user_id, datetime.now())
            
        except Exception as e:
            logger.error(f"🇬🇳 Erreur envoi message foundation: {e}")
    
    async def get_foundation_stats(self) -> Dict[str, Any]:
        """Récupère les statistiques complètes de la foundation."""
        try:
            # Calculer les statistiques avancées
            avg_donation = 0.0
            if self.donation_history:
                total_donations = sum(d["foundation_amount"] for d in self.donation_history)
                avg_donation = total_donations / len(self.donation_history)
            
            # Top donateurs du mois
            current_month = datetime.now().replace(day=1)
            monthly_donors = [
                d for d in self.donation_history 
                if d["timestamp"] >= current_month
            ]
            
            top_donors = {}
            for donation in monthly_donors:
                user_id = donation["user_id"]
                username = donation["username"]
                amount = donation["foundation_amount"]
                
                if user_id not in top_donors:
                    top_donors[user_id] = {"username": username, "amount": 0.0}
                top_donors[user_id]["amount"] += amount
            
            # Trier par montant
            top_donors = sorted(top_donors.items(), key=lambda x: x[1]["amount"], reverse=True)[:10]
            
            return {
                "total_collected": self.total_collected,
                "monthly_collected": self.monthly_collected,
                "daily_collected": self.daily_collected,
                "total_donations": len(self.donation_history),
                "avg_donation": avg_donation,
                "impact_stats": self.impact_stats,
                "top_donors": [{"user_id": uid, **data} for uid, data in top_donors],
                "last_updated": datetime.now()
            }
            
        except Exception as e:
            logger.error(f"🇬🇳 Erreur statistiques foundation: {e}")
            return {"error": str(e)}
    
    async def get_user_foundation_stats(self, user_id: int) -> Dict[str, Any]:
        """Récupère les statistiques foundation d'un utilisateur."""
        try:
            # Filtrer les donations de l'utilisateur
            user_donations = [
                d for d in self.donation_history 
                if d["user_id"] == user_id
            ]
            
            if not user_donations:
                return {
                    "user_id": user_id,
                    "total_donated": 0.0,
                    "donation_count": 0,
                    "avg_donation": 0.0,
                    "last_donation": None,
                    "gain_types": {}
                }
            
            total_donated = sum(d["foundation_amount"] for d in user_donations)
            donation_count = len(user_donations)
            avg_donation = total_donated / donation_count
            last_donation = max(d["timestamp"] for d in user_donations)
            
            # Regrouper par type de gain
            gain_types = {}
            for donation in user_donations:
                gain_type = donation["gain_type"]
                if gain_type not in gain_types:
                    gain_types[gain_type] = {"count": 0, "total": 0.0}
                gain_types[gain_type]["count"] += 1
                gain_types[gain_type]["total"] += donation["foundation_amount"]
            
            return {
                "user_id": user_id,
                "total_donated": total_donated,
                "donation_count": donation_count,
                "avg_donation": avg_donation,
                "last_donation": last_donation,
                "gain_types": gain_types
            }
            
        except Exception as e:
            logger.error(f"🇬🇳 Erreur stats utilisateur foundation: {e}")
            return {"error": str(e)}
    
    async def _daily_reset(self):
        """Réinitialisation quotidienne des compteurs."""
        logger.info("🇬🇳 Démarrage reset quotidien foundation...")
        
        while True:
            try:
                # Attendre minuit
                now = datetime.now()
                tomorrow = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
                sleep_time = (tomorrow - now).total_seconds()
                
                await asyncio.sleep(sleep_time)
                
                # Reset du compteur quotidien
                self.daily_collected = 0.0
                
                logger.info("🇬🇳 Reset quotidien foundation effectué")
                
            except Exception as e:
                logger.error(f"🇬🇳 Erreur reset quotidien: {e}")
                await asyncio.sleep(3600)
    
    async def _monthly_reset(self):
        """Réinitialisation mensuelle des compteurs."""
        logger.info("🇬🇳 Démarrage reset mensuel foundation...")
        
        while True:
            try:
                # Attendre le premier du mois prochain
                now = datetime.now()
                next_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0) + timedelta(days=32)
                next_month = next_month.replace(day=1)
                sleep_time = (next_month - now).total_seconds()
                
                await asyncio.sleep(sleep_time)
                
                # Reset du compteur mensuel
                self.monthly_collected = 0.0
                
                logger.info("🇬🇳 Reset mensuel foundation effectué")
                
            except Exception as e:
                logger.error(f"🇬🇳 Erreur reset mensuel: {e}")
                await asyncio.sleep(3600)
    
    async def _impact_calculator(self):
        """Calculateur d'impact en temps réel."""
        logger.info("🇬🇳 Démarrage calculateur d'impact...")
        
        while True:
            try:
                # Mettre à jour les statistiques d'impact toutes les heures
                await self._recalculate_impact()
                
                await asyncio.sleep(3600)  # 1 heure
                
            except Exception as e:
                logger.error(f"🇬🇳 Erreur calculateur impact: {e}")
                await asyncio.sleep(3600)
    
    async def _recalculate_impact(self):
        """Recalcule l'impact basé sur les donations réelles."""
        try:
            # Recalculer basé sur l'historique complet
            total_amount = sum(d["foundation_amount"] for d in self.donation_history)
            
            # Recalculer les stats d'impact
            self.impact_stats = {
                "children_helped": int(total_amount * 1.0),
                "meals_provided": int(total_amount * 2.0),
                "school_supplies": int(total_amount * 0.5),
                "families_supported": int(total_amount * 0.2),
                "orphans_housed": int(total_amount * 0.1)
            }
            
            # Sauvegarder
            await database.update_foundation_stats({
                "impact_stats": self.impact_stats,
                "last_updated": datetime.now()
            })
            
        except Exception as e:
            logger.error(f"🇬🇳 Erreur recalcul impact: {e}")
    
    async def generate_impact_report(self) -> str:
        """Génère un rapport d'impact détaillé."""
        try:
            stats = await self.get_foundation_stats()
            
            if "error" in stats:
                return "❌ Erreur lors de la génération du rapport"
            
            report = (
                f"🇬🇳 **RAPPORT D'IMPACT CHICO FOUNDATION** 🇬🇳\n\n"
                f"💰 *Financements récoltés* 💰\n"
                f"🌍 *Total :* {stats['total_collected']:.2f}$\n"
                f"📅 *Ce mois :* {stats['monthly_collected']:.2f}$\n"
                f"📊 *Aujourd'hui :* {stats['daily_collected']:.2f}$\n"
                f"🔢 *Donations :* {stats['total_donations']}\n"
                f"💝 *Moyenne :* {stats['avg_donation']:.2f}$\n\n"
                f"❤️ *Impact réel en Guinée* ❤️\n"
                f"👶 *Enfants aidés :* {stats['impact_stats']['children_helped']}\n"
                f"🍽️ *Repas fournis :* {stats['impact_stats']['meals_provided']}\n"
                f"📚 *Fournitures scolaires :* {stats['impact_stats']['school_supplies']}\n"
                f"👨‍👩‍👧‍👦 *Familles soutenues :* {stats['impact_stats']['families_supported']}\n"
                f"🏠 *Orphelins logés :* {stats['impact_stats']['orphans_housed']}\n\n"
                f"🏆 *Top donateurs du mois* 🏆\n"
            )
            
            # Ajouter les top donateurs
            for i, donor in enumerate(stats['top_donors'][:5], 1):
                report += f"🥇 *{i}. {donor['username']} :* {donor['amount']:.2f}$\n"
            
            report += f"\n🇬🇳 *La Guinée se soulève ensemble !* 🇬🇳"
            
            return report
            
        except Exception as e:
            logger.error(f"🇬🇳 Erreur génération rapport impact: {e}")
            return "❌ Erreur lors de la génération du rapport"

# Instance globale du service foundation
chico_foundation = ChicoFoundation()

# Handlers de commandes foundation
@foundation_router.message(Command("foundation"))
async def handle_foundation_command(message: types.Message) -> None:
    """Gère la commande /foundation."""
    user_id = message.from_user.id
    
    # Récupérer les statistiques de la foundation
    stats = await chico_foundation.get_foundation_stats()
    
    if "error" in stats:
        await message.answer(
            "❌ *Erreur lors du chargement des statistiques* ❌",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    # Récupérer les stats de l'utilisateur
    user_stats = await chico_foundation.get_user_foundation_stats(user_id)
    
    # Formater le message
    foundation_message = (
        f"❤️ **CHICO FOUNDATION** ❤️\n\n"
        f"🇬🇳 *Grâce à vous, la Chico Foundation a déjà récolté* 🇬🇳\n"
        f"💰 **{stats['total_collected']:.2f}$** 💰\n\n"
        f"📊 *Statistiques du mois* 📊\n"
        f"📅 *Récolté ce mois :* {stats['monthly_collected']:.2f}$\n"
        f"📈 *Aujourd'hui :* {stats['daily_collected']:.2f}$\n"
        f"🔢 *Nombre de donations :* {stats['total_donations']}\n\n"
        f"❤️ *Ton impact personnel* ❤️\n"
        f"💝 *Tu as donné :* {user_stats['total_donated']:.2f}$\n"
        f"🎯 *Nombre de donations :* {user_stats['donation_count']}\n"
        f"📊 *Moyenne par donation :* {user_stats['avg_donation']:.2f}$\n\n"
        f"🌍 *Impact en Guinée* 🌍\n"
        f"👶 *Enfants aidés :* {stats['impact_stats']['children_helped']}\n"
        f"🍽️ *Repas fournis :* {stats['impact_stats']['meals_provided']}\n"
        f"📚 *Fournitures scolaires :* {stats['impact_stats']['school_supplies']}\n"
        f"👨‍👩‍👧‍👦 *Familles soutenues :* {stats['impact_stats']['families_supported']}\n"
        f"🏠 *Orphelins logés :* {stats['impact_stats']['orphans_housed']}\n\n"
        f"🇬🇳 *La Guinée se soulève ensemble, une transaction à la fois* 🇬🇳\n"
        f"❤️ *Merci d'être la Chico Family* ❤️"
    )
    
    await message.answer(foundation_message, parse_mode=ParseMode.MARKDOWN)

@foundation_router.message(Command("impact"))
async def handle_impact_command(message: types.Message) -> None:
    """Gère la commande /impact."""
    # Générer le rapport d'impact détaillé
    report = await chico_foundation.generate_impact_report()
    
    await message.answer(report, parse_mode=ParseMode.MARKDOWN)

# Tests d'intégration
if __name__ == "__main__":
    import random
    import unittest
    from unittest import IsolatedAsyncioTestCase
    
    class TestChicoFoundation(IsolatedAsyncioTestCase):
        """Tests d'intégration pour la Chico Foundation."""
        
        async def asyncSetUp(self):
            """Configuration des tests."""
            self.foundation = ChicoFoundation()
            await self.foundation.initialize()
        
        async def test_foundation_initialization(self):
            """Teste l'initialisation de la foundation."""
            self.assertTrue(self.foundation.is_initialized)
            self.assertEqual(FOUNDATION_RATE, 0.01)
            self.assertEqual(FOUNDATION_MESSAGE_COOLDOWN, 86400)
            
            print("\n❤️ Chico Foundation initialisée")
        
        async def test_gain_processing(self):
            """Teste le traitement des gains."""
            user_id = 12345
            username = "test_user"
            gain_amount = 100.0
            gain_type = "bounty"
            
            result = await self.foundation.process_gain(user_id, username, gain_amount, gain_type)
            
            self.assertTrue(result["success"])
            self.assertEqual(result["original_gain"], gain_amount)
            self.assertEqual(result["foundation_amount"], 1.0)  # 1% de 100$
            self.assertEqual(result["user_net_amount"], 99.0)
            self.assertEqual(result["gain_type"], gain_type)
            
            print("\n💰 Traitement gain testé")
        
        async def test_multiple_gain_types(self):
            """Teste différents types de gains."""
            user_id = 12346
            username = "test_user2"
            
            # Test bounty
            result1 = await self.foundation.process_gain(user_id, username, 200.0, "bounty")
            self.assertTrue(result1["success"])
            self.assertEqual(result1["foundation_amount"], 2.0)
            
            # Test trading
            result2 = await self.foundation.process_gain(user_id, username, 500.0, "trading")
            self.assertTrue(result2["success"])
            self.assertEqual(result2["foundation_amount"], 5.0)
            
            # Test investment
            result3 = await self.foundation.process_gain(user_id, username, 1000.0, "investment")
            self.assertTrue(result3["success"])
            self.assertEqual(result3["foundation_amount"], 10.0)
            
            print("\n📊 Types de gains testés")
        
        async def test_foundation_stats(self):
            """Teste les statistiques de la foundation."""
            # Ajouter quelques donations
            await self.foundation.process_gain(12347, "user1", 100.0, "bounty")
            await self.foundation.process_gain(12348, "user2", 200.0, "trading")
            await self.foundation.process_gain(12349, "user3", 300.0, "investment")
            
            stats = await self.foundation.get_foundation_stats()
            
            self.assertNotIn("error", stats)
            self.assertIn("total_collected", stats)
            self.assertIn("monthly_collected", stats)
            self.assertIn("daily_collected", stats)
            self.assertIn("impact_stats", stats)
            
            # Vérifier le total
            expected_total = 1.0 + 2.0 + 3.0  # 1% de chaque gain
            self.assertEqual(stats["total_collected"], expected_total)
            
            print("\n📊 Statistiques foundation testées")
        
        async def test_user_stats(self):
            """Teste les statistiques utilisateur."""
            user_id = 12350
            username = "test_user_stats"
            
            # Ajouter plusieurs donations pour le même utilisateur
            await self.foundation.process_gain(user_id, username, 100.0, "bounty")
            await self.foundation.process_gain(user_id, username, 200.0, "trading")
            await self.foundation.process_gain(user_id, username, 300.0, "investment")
            
            user_stats = await self.foundation.get_user_foundation_stats(user_id)
            
            self.assertNotIn("error", user_stats)
            self.assertEqual(user_stats["user_id"], user_id)
            self.assertEqual(user_stats["donation_count"], 3)
            self.assertEqual(user_stats["total_donated"], 6.0)  # 1 + 2 + 3
            self.assertEqual(user_stats["avg_donation"], 2.0)
            
            # Vérifier les types de gains
            self.assertIn("bounty", user_stats["gain_types"])
            self.assertIn("trading", user_stats["gain_types"])
            self.assertIn("investment", user_stats["gain_types"])
            
            print("\n👤 Statistiques utilisateur testées")
        
        async def test_message_cooldown(self):
            """Teste le cooldown des messages."""
            user_id = 12351
            username = "test_cooldown"
            
            # Premier gain - devrait envoyer un message
            result1 = await self.foundation.process_gain(user_id, username, 100.0, "bounty")
            self.assertTrue(result1["message_sent"])
            
            # Deuxième gain immédiat - ne devrait pas envoyer de message
            result2 = await self.foundation.process_gain(user_id, username, 100.0, "bounty")
            self.assertFalse(result2["message_sent"])
            
            print("\n⏰ Cooldown messages testé")
        
        async def test_impact_calculation(self):
            """Teste le calcul de l'impact."""
            # Ajouter un gain significatif
            await self.foundation.process_gain(12352, "impact_test", 1000.0, "bounty")
            
            # Vérifier l'impact
            impact = self.foundation.impact_stats
            
            # 10$ de donation = 10 enfants aidés, 20 repas, etc.
            self.assertGreater(impact["children_helped"], 0)
            self.assertGreater(impact["meals_provided"], 0)
            self.assertGreater(impact["school_supplies"], 0)
            
            print("\n🌍 Calcul impact testé")
        
        async def test_zero_gain_handling(self):
            """Teste la gestion des gains nuls ou négatifs."""
            user_id = 12353
            username = "zero_gain"
            
            # Gain nul
            result1 = await self.foundation.process_gain(user_id, username, 0.0, "bounty")
            self.assertFalse(result1["success"])
            
            # Gain négatif
            result2 = await self.foundation.process_gain(user_id, username, -100.0, "bounty")
            self.assertFalse(result2["success"])
            
            print("\n⚠️ Gains nuls/négatifs testés")
        
        async def test_foundation_rate(self):
            """Teste le taux de prélèvement."""
            test_amounts = [50.0, 100.0, 250.0, 500.0, 1000.0]
            
            for amount in test_amounts:
                user_id = int(12354 + amount)
                result = await self.foundation.process_gain(user_id, f"user_{amount}", amount, "bounty")
                
                expected_foundation = amount * FOUNDATION_RATE
                self.assertEqual(result["foundation_amount"], expected_foundation)
                self.assertEqual(result["user_net_amount"], amount - expected_foundation)
            
            print("\n💸 Taux de prélèvement testé")
        
        async def test_impact_report_generation(self):
            """Teste la génération du rapport d'impact."""
            # Ajouter quelques donations
            for i in range(5):
                await self.foundation.process_gain(12355 + i, f"user_report_{i}", 100.0, "bounty")
            
            report = await self.foundation.generate_impact_report()
            
            self.assertNotIn("Erreur", report)
            self.assertIn("CHICO FOUNDATION", report)
            self.assertIn("Financements récoltés", report)
            self.assertIn("Impact réel en Guinée", report)
            
            print("\n📋 Génération rapport testée")
        
        async def test_concurrent_processing(self):
            """Teste le traitement concurrent des gains."""
            user_ids = [12360, 12361, 12362, 12363, 12364]
            
            # Traiter plusieurs gains en parallèle
            tasks = []
            for i, user_id in enumerate(user_ids):
                task = self.foundation.process_gain(user_id, f"concurrent_{i}", 100.0, "bounty")
                tasks.append(task)
            
            results = await asyncio.gather(*tasks)
            
            # Vérifier que tous les traitements ont réussi
            for result in results:
                self.assertTrue(result["success"])
                self.assertEqual(result["foundation_amount"], 1.0)
            
            print("\n⚡ Traitement concurrent testé")
        
        async def test_foundation_message_content(self):
            """Teste le contenu du message foundation."""
            # Vérifier que le message contient les éléments requis
            self.assertIn("1 % de ton gain", FOUNDATION_MESSAGE)
            self.assertIn("Chico Foundation", FOUNDATION_MESSAGE)
            self.assertIn("Kamsar et Conakry", FOUNDATION_MESSAGE)
            self.assertIn("mamans seules", FOUNDATION_MESSAGE)
            self.assertIn("jeunes filles", FOUNDATION_MESSAGE)
            self.assertIn("orphelins", FOUNDATION_MESSAGE)
            self.assertIn("Chico & Problematique", FOUNDATION_MESSAGE)
            self.assertIn("Chico Family", FOUNDATION_MESSAGE)
            self.assertIn("🇬🇳❤️", FOUNDATION_MESSAGE)
            
            print("\n💬 Contenu message foundation testé")
    
    # Exécuter les tests
    unittest.main()
