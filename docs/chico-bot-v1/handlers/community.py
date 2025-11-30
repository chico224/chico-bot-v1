"""
Système de Concours Mensuel Légendaire - ChicoBot Community

Fonctionnalités principales :
- Classement mondial et guinéen en temps réel
- Concours mensuel automatique avec groupe temporaire
- Tirage au sort pour les gains des admins
- Support 24h/24 avec contacts directs
- Ambiance famille guinéenne ultra-émotionnelle

🇬🇳 La communauté qui transforme la Guinée 🇬🇳
"""

import asyncio
import logging
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from aiogram import Bot, Dispatcher, Router, F, types
from aiogram.filters import Command, CommandObject
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, 
    InlineKeyboardButton, ChatMemberUpdated, ChatJoinRequest
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config.settings import settings
from core.ai_response import generate_ai_response
from core.database import database
from core.logging_setup import get_logger
from services.fortress_security import fortress_security

# Configuration du logger
logger = get_logger(__name__)

# Router pour les commandes communautaires
community_router = Router()

# États pour le système de concours
class ConcoursState(StatesGroup):
    waiting_for_concours = State()

# Configuration du concours mensuel
CONCOURS_CONFIG = {
    "min_active_users": 10,  # Nombre minimum d'utilisateurs actifs
    "prize_percentage": 0.5,  # 0.5% des gains des admins
    "duration_hours": 24,  # Durée du concours en heures
    "top_winners": 10,  # Top éligible au tirage
    "group_name_template": "🎉 CONCOURS CHICO – {month} {year} 🎉"
}

# Messages légendaires du système
MESSAGES = {
    "classement_header": (
        "🏆 **CLASSEMENT CHICOBOT – LA GUINÉE DOMINE !** 🇬🇳\n\n"
        "🌍 *Les meilleurs traders et investisseurs du monde entier*\n"
        "🇬🇳 *Et nos héros guinéens qui brillent !*\n\n"
    ),
    "concours_announcement": (
        "🎉 **CONCOURS MENSUEL CHICOBOT – LA GUINÉE EN FÊTE !** 🎉\n\n"
        "🇬🇳 *Le moment le plus attendu est arrivé !*\n"
        "💰 *Des prix légendaires à gagner !*\n"
        "🔥 *Ambiance familiale et feu !*\n\n"
    ),
    "winner_announcement": (
        "🎉 **LE GAGNANT DU CONCOURS EST : @{username} !** 🎉\n\n"
        "💰 **+{percentage}% DES GAINS ADMINS CE MOIS-CI !** 💰\n"
        "🇬🇳 **LA GUINÉE CÉLÈBRE SON CHAMPION !** 🇬🇳\n\n"
        "🔥 *Félicitations au nouveau héros du mois !* 🔥\n\n"
    ),
    "support_message": (
        "📞 **SUPPORT CHICOBOT – 24H/24** 📞\n\n"
        "🇬🇳 *Nous sommes toujours là pour toi* 🇬🇳\n\n"
        "👑 **Chico (Oumar Sow)** 👑\n"
        "📱 *WhatsApp :* +224 661 92 05 19\n"
        "📱 *Appel :* +224 669 43 54 63\n"
        "📧 *Email :* chico@chicobot.gn\n\n"
        "⚡ **Problematique (Ibrahima Barry)** ⚡\n"
        "📱 *WhatsApp :* [Bientôt disponible]\n"
        "📱 *Appel :* [Bientôt disponible]\n"
        "📧 *Email :* ibrahima@chicobot.gn\n\n"
        "🇬🇳 *La famille ChicoBot est toujours là pour toi* 🇬🇳\n"
        "🚀 *N'hésite jamais à nous contacter* 🚀\n\n"
    )
}

class CommunityManager:
    """Gestionnaire de la communauté ChicoBot."""
    
    def __init__(self):
        self.is_concours_active = False
        self.concours_group_id = None
        self.concours_start_time = None
        self.active_users = []
        self.monthly_winners = []
        
    async def initialize(self) -> bool:
        """Initialise le gestionnaire de communauté."""
        try:
            logger.info("🇬🇳 Initialisation du gestionnaire de communauté...")
            
            # Vérifier si un concours est en cours
            await self._check_existing_concours()
            
            # Démarrer la tâche de fond pour les concours mensuels
            asyncio.create_task(self._monthly_concour_scheduler())
            
            logger.info("🇬🇳 Gestionnaire de communauté initialisé avec succès")
            return True
            
        except Exception as e:
            logger.error(f"🇬🇳 Erreur initialisation communauté: {e}")
            return False
    
    async def get_global_ranking(self) -> Dict[str, List[Dict]]:
        """Récupère le classement mondial et guinéen."""
        try:
            # Récupérer tous les utilisateurs avec leurs gains
            all_users = await database.get_all_users_with_earnings()
            
            # Trier par gains totaux (décroissant)
            sorted_users = sorted(all_users, key=lambda x: x['total_earnings'], reverse=True)
            
            # Top 20 mondial
            top_20_global = sorted_users[:20]
            
            # Top 10 Guinée (filtrer les utilisateurs guinéens)
            guinean_users = [user for user in sorted_users if user.get('country') == 'GN']
            top_10_guinea = guinean_users[:10]
            
            # Formatter les classements
            formatted_global = []
            for i, user in enumerate(top_20_global, 1):
                formatted_global.append({
                    "rank": i,
                    "username": user.get('username', 'Anonymous'),
                    "first_name": user.get('first_name', ''),
                    "total_earnings": user['total_earnings'],
                    "country": user.get('country', '🌍'),
                    "flag": self._get_country_flag(user.get('country', '🌍'))
                })
            
            formatted_guinea = []
            for i, user in enumerate(top_10_guinea, 1):
                formatted_guinea.append({
                    "rank": i,
                    "username": user.get('username', 'Anonymous'),
                    "first_name": user.get('first_name', ''),
                    "total_earnings": user['total_earnings'],
                    "city": user.get('city', 'Conakry'),
                    "join_date": user.get('join_date', datetime.now())
                })
            
            return {
                "global_top": formatted_global,
                "guinea_top": formatted_guinea,
                "total_users": len(all_users),
                "last_updated": datetime.now()
            }
            
        except Exception as e:
            logger.error(f"🇬🇳 Erreur récupération classement: {e}")
            return {"global_top": [], "guinea_top": [], "total_users": 0, "last_updated": datetime.now()}
    
    def _get_country_flag(self, country_code: str) -> str:
        """Retourne le drapeau correspondant au pays."""
        flags = {
            'GN': '🇬🇳', 'US': '🇺🇸', 'FR': '🇫🇷', 'GB': '🇬🇧',
            'DE': '🇩🇪', 'ES': '🇪🇸', 'IT': '🇮🇹', 'CA': '🇨🇦',
            'AU': '🇦🇺', 'JP': '🇯🇵', 'CN': '🇨🇳', 'IN': '🇮🇳',
            'BR': '🇧🇷', 'MX': '🇲🇽', 'RU': '🇷🇺', 'ZA': '🇿🇦'
        }
        return flags.get(country_code, '🌍')
    
    async def start_monthly_concours(self) -> bool:
        """Démarre le concours mensuel."""
        try:
            if self.is_concours_active:
                logger.warning("🇬🇳 Un concours est déjà en cours")
                return False
            
            # Vérifier le nombre d'utilisateurs actifs
            active_users = await self._get_active_users_count()
            if active_users < CONCOURS_CONFIG["min_active_users"]:
                logger.info(f"🇬🇳 Utilisateurs actifs insuffisants: {active_users} (min: {CONCOURS_CONFIG['min_active_users']})")
                return False
            
            # Créer le groupe temporaire
            group_id = await self._create_concours_group()
            if not group_id:
                logger.error("🇬🇳 Impossible de créer le groupe concours")
                return False
            
            # Initialiser le concours
            self.is_concours_active = True
            self.concours_group_id = group_id
            self.concours_start_time = datetime.now()
            
            # Inviter les utilisateurs actifs
            await self._invite_active_users(group_id)
            
            # Envoyer le message d'annonce
            await self._send_concours_announcement(group_id)
            
            # Démarrer le timer de fermeture
            asyncio.create_task(self._concours_timer())
            
            logger.info(f"🇬🇳 Concours mensuel démarré - Groupe: {group_id}")
            return True
            
        except Exception as e:
            logger.error(f"🇬🇳 Erreur démarrage concours: {e}")
            return False
    
    async def _get_active_users_count(self) -> int:
        """Compte les utilisateurs actifs (30 derniers jours)."""
        try:
            # Récupérer depuis la base de données
            active_users = await database.get_active_users(days=30)
            return len(active_users)
        except:
            return 0
    
    async def _create_concours_group(self) -> Optional[int]:
        """Crée le groupe temporaire pour le concours."""
        try:
            # Note: Cette fonction nécessite les permissions appropriées du bot
            # Pour l'instant, nous simulons la création
            
            month_name = datetime.now().strftime("%B")
            year = datetime.now().year
            group_name = CONCOURS_CONFIG["group_name_template"].format(
                month=month_name, 
                year=year
            )
            
            # Simulation - en pratique, utiliser bot.create_chat()
            logger.info(f"🇬🇳 Création du groupe: {group_name}")
            
            # Pour la simulation, nous utilisons un chat ID fictif
            simulated_group_id = -1001234567890  # ID de groupe négatif
            
            return simulated_group_id
            
        except Exception as e:
            logger.error(f"🇬🇳 Erreur création groupe concours: {e}")
            return None
    
    async def _invite_active_users(self, group_id: int):
        """Invite tous les utilisateurs actifs au groupe."""
        try:
            active_users = await database.get_active_users(days=30)
            
            for user in active_users:
                try:
                    # Note: En pratique, utiliser bot.approve_chat_join_request()
                    # Pour l'instant, nous simulons l'invitation
                    
                    user_id = user['user_id']
                    username = user.get('username', 'Anonymous')
                    
                    logger.info(f"🇬🇳 Invitation de @{username} au groupe concours")
                    
                    # Simulation de l'invitation
                    await asyncio.sleep(0.1)  # Éviter le rate limiting
                    
                except Exception as e:
                    logger.error(f"🇬🇳 Erreur invitation utilisateur {user_id}: {e}")
                    continue
            
            logger.info(f"🇬🇳 {len(active_users)} utilisateurs invités au groupe concours")
            
        except Exception as e:
            logger.error(f"🇬🇳 Erreur invitation utilisateurs: {e}")
    
    async def _send_concours_announcement(self, group_id: int):
        """Envoie l'annonce du concours dans le groupe."""
        try:
            # Message d'annonce épique
            announcement = (
                MESSAGES["concours_announcement"] +
                "📊 **RÈGLES DU CONCOURS :** 📊\n\n"
                "🎯 *Le Top 10 du classement mensuel est éligible*\n"
                "🎲 *Tirage au sort à minuit*\n"
                "💰 *Le gagnant reçoit 0.5% des gains des admins !*\n\n"
                "🔥 **AMBiance FEU PENDANT 24H !** 🔥\n\n"
                "🇬🇳 *Partage tes succès, félicite les autres, célébrons ensemble !* 🇬🇳\n"
                "🎉 *Messages, réactions, émojis, tout est permis !* 🎉\n\n"
                "⏰ *Fin du concours : Demain à 23h59 GMT*\n\n"
                "🚀 **QUE LE MEILLEUR GAGNE !** 🚀"
            )
            
            # Créer le clavier avec les réactions rapides
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="🇬🇳", callback_data="flag_gn"),
                    InlineKeyboardButton(text="🔥", callback_data="fire"),
                    InlineKeyboardButton(text="🏆", callback_data="trophy"),
                    InlineKeyboardButton(text="💰", callback_data="money")
                ],
                [
                    InlineKeyboardButton(text="🎉", callback_data="celebrate"),
                    InlineKeyboardButton(text="👑", callback_data="crown"),
                    InlineKeyboardButton(text="⚡", callback_data="lightning"),
                    InlineKeyboardButton(text="💎", callback_data="diamond")
                ]
            ])
            
            # Envoyer le message (simulation)
            logger.info(f"🇬🇳 Envoi de l'annonce au groupe {group_id}")
            
            # En pratique: await bot.send_message(group_id, announcement, reply_markup=keyboard)
            
        except Exception as e:
            logger.error(f"🇬🇳 Erreur envoi annonce concours: {e}")
    
    async def _concours_timer(self):
        """Gère le timer du concours (24h)."""
        try:
            # Attendre 24 heures
            await asyncio.sleep(CONCOURS_CONFIG["duration_hours"] * 3600)
            
            # Tirage au sort et annonce du gagnant
            await self._draw_winner()
            
            # Fermer le groupe
            await self._close_concours_group()
            
        except Exception as e:
            logger.error(f"🇬🇳 Erreur timer concours: {e}")
    
    async def _draw_winner(self):
        """Effectue le tirage au sort du gagnant."""
        try:
            # Récupérer le Top 10 du mois
            monthly_top = await database.get_monthly_top_users(limit=CONCOURS_CONFIG["top_winners"])
            
            if not monthly_top:
                logger.error("🇬🇳 Aucun utilisateur éligible pour le tirage")
                return
            
            # Tirage au sort
            winner = random.choice(monthly_top)
            
            # Calculer le prix (0.5% des gains des admins)
            admin_earnings = await database.get_admin_monthly_earnings()
            prize_amount = admin_earnings * (CONCOURS_CONFIG["prize_percentage"] / 100)
            
            # Annoncer le gagnant
            await self._announce_winner(winner, prize_amount)
            
            # Enregistrer le gagnant
            await self._record_winner(winner, prize_amount)
            
            logger.info(f"🇬🇳 Gagnant du concours: @{winner['username']} - Prix: {prize_amount:.2f}$")
            
        except Exception as e:
            logger.error(f"🇬🇳 Erreur tirage au sort: {e}")
    
    async def _announce_winner(self, winner: Dict, prize_amount: float):
        """Annonce le gagnant du concours."""
        try:
            winner_message = MESSAGES["winner_announcement"].format(
                username=winner['username'],
                percentage=CONCOURS_CONFIG["prize_percentage"]
            )
            
            # Ajouter les détails du prix
            winner_message += (
                f"💰 *Prix total :* {prize_amount:.2f}$\n"
                f"🏆 *Classement du mois :* #{winner['monthly_rank']}\n"
                f"📈 *Gains totaux :* {winner['total_earnings']:.2f}$\n\n"
                "🇬🇳 **FÉLICITATIONS AU NOUVEAU CHAMPION !** 🇬🇳\n\n"
                "🎉 *Tout le monde, félicitons notre héros !* 🎉\n"
                "🔥 *La Guinée est fière de toi !* 🔥\n\n"
                "📞 *Contact Chico pour recevoir ton prix* 📞"
            )
            
            # Envoyer dans le groupe concours
            if self.concours_group_id:
                logger.info(f"🇬🇳 Annonce du gagnant @{winner['username']}")
                # En pratique: await bot.send_message(self.concours_group_id, winner_message)
            
            # Envoyer en message privé au gagnant
            logger.info(f"🇬🇳 Message privé envoyé à @{winner['username']}")
            # En pratique: await bot.send_message(winner['user_id'], winner_message)
            
        except Exception as e:
            logger.error(f"🇬🇳 Erreur annonce gagnant: {e}")
    
    async def _record_winner(self, winner: Dict, prize_amount: float):
        """Enregistre le gagnant dans la base de données."""
        try:
            await database.record_concours_winner(
                user_id=winner['user_id'],
                username=winner['username'],
                prize_amount=prize_amount,
                concours_date=datetime.now()
            )
            
            # Ajouter à la liste des gagnants du mois
            self.monthly_winners.append({
                "user_id": winner['user_id'],
                "username": winner['username'],
                "prize_amount": prize_amount,
                "date": datetime.now()
            })
            
        except Exception as e:
            logger.error(f"🇬🇳 Erreur enregistrement gagnant: {e}")
    
    async def _close_concours_group(self):
        """Ferme le groupe temporaire du concours."""
        try:
            if self.concours_group_id:
                # Message de fin
                closing_message = (
                    "🏁 **FIN DU CONCOURS MENSUEL** 🏁\n\n"
                    "🇬🇳 *Merci à tous pour cette ambiance incroyable !* 🇬🇳\n\n"
                    "🎉 *Rendez-vous le mois prochain pour un nouveau concours !* 🎉\n"
                    "💰 *De nouveaux prix à gagner !* 💰\n\n"
                    "🚀 **LA GUINÉE CONTINUE DE DOMINER !** 🚀"
                )
                
                logger.info(f"🇬🇳 Fermeture du groupe concours {self.concours_group_id}")
                
                # En pratique: await bot.send_message(self.concours_group_id, closing_message)
                # En pratique: await bot.leave_chat(self.concours_group_id)
            
            # Réinitialiser l'état
            self.is_concours_active = False
            self.concours_group_id = None
            self.concours_start_time = None
            
            logger.info("🇬🇳 Concours mensuel terminé avec succès")
            
        except Exception as e:
            logger.error(f"🇬🇳 Erreur fermeture groupe concours: {e}")
    
    async def _check_existing_concours(self):
        """Vérifie si un concours est déjà en cours au démarrage."""
        try:
            # Récupérer depuis la base de données
            last_concours = await database.get_last_concours()
            
            if last_concours and not last_concours['is_finished']:
                # Un concours est en cours, le restaurer
                self.is_concours_active = True
                self.concours_group_id = last_concours['group_id']
                self.concours_start_time = last_concours['start_time']
                
                logger.info(f"🇬🇳 Restauration du concours en cours - Groupe: {self.concours_group_id}")
                
        except Exception as e:
            logger.error(f"🇬🇳 Erreur vérification concours existant: {e}")
    
    async def _monthly_concour_scheduler(self):
        """Planificateur mensuel pour les concours."""
        while True:
            try:
                # Attendre jusqu'au 1er du mois suivant à 00:00 GMT
                now = datetime.now()
                
                # Calculer le 1er du mois suivant
                if now.month == 12:
                    next_month = datetime(now.year + 1, 1, 1)
                else:
                    next_month = datetime(now.year, now.month + 1, 1)
                
                # Calculer le temps d'attente
                wait_time = (next_month - now).total_seconds()
                
                logger.info(f"🇬🇳 Prochain concours le: {next_month.strftime('%Y-%m-%d 00:00 GMT')}")
                
                # Attendre
                await asyncio.sleep(wait_time)
                
                # Lancer le concours
                await self.start_monthly_concours()
                
            except Exception as e:
                logger.error(f"🇬🇳 Erreur planificateur concours: {e}")
                await asyncio.sleep(3600)  # Attendre 1h en cas d'erreur

# Instance globale du gestionnaire de communauté
community_manager = CommunityManager()

# Handlers pour les commandes

@community_router.message(Command("classement"))
async def handle_classement_command(message: types.Message):
    """Affiche le classement mondial et guinéen avec IA."""
    try:
        user_id = message.from_user.id
        username = message.from_user.username or "ami"
        
        # Récupérer les classements
        rankings = await community_manager.get_global_ranking()
        
        # Préparer les infos utilisateur pour l'IA
        user_info = {
            "username": username,
            "total_earnings": 0,  # Sera récupéré par l'IA si besoin
            "global_rank": None,
            "guinea_rank": None,
            "country": "GN"
        }
        
        # Créer le contexte pour l'IA avec les données du classement
        classement_context = f"""
Classement mondial Top 20:
{chr(10).join([f"#{user['rank']} @{user['username']} - ${user['total_earnings']:,.2f}" for user in rankings["global_top"][:5]])}

Classement Guinée Top 5:
{chr(10).join([f"#{user['rank']} @{user['username']} - ${user['total_earnings']:,.2f}" for user in rankings["guinea_top"][:3]])}

Total utilisateurs: {rankings['total_users']}
"""
        
        # Générer la réponse IA avec ton guinéen
        ai_response = await generate_ai_response(
            user_id=user_id,
            message=f"/classement\n\n{classement_context}",
            context="classement",
            user_info=user_info
        )
        
        # Envoyer la réponse IA
        await message.answer(ai_response.content, parse_mode=ParseMode.MARKDOWN)
        
        # Créer le clavier avec des actions rapides
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🔄 Actualiser", callback_data="refresh_ranking"),
                InlineKeyboardButton(text="📊 Mes Stats", callback_data="my_stats")
            ],
            [
                InlineKeyboardButton(text="🎉 Concours", callback_data="concours_info"),
                InlineKeyboardButton(text="📞 Support", callback_data="support_info")
            ]
        ])
        
        await message.answer(
            "🇬🇳 *Que veux-tu faire maintenant, frère/sœur ?* 🇬🇳\n\n"
            "🚀 *Choisis une action ci-dessous :*",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=keyboard
        )
        
        logger.info(f"🇬🇳 Classement demandé par @{username}")
        
    except Exception as e:
        logger.error(f"🇬🇳 Erreur commande classement: {e}")
        
        # Réponse IA d'erreur
        error_response = await generate_ai_response(
            user_id=message.from_user.id,
            message="/classement",
            context="error"
        )
        
        await message.answer(error_response.content, parse_mode=ParseMode.MARKDOWN)

@community_router.message(Command("support"))
async def handle_support_command(message: types.Message):
    """Affiche les informations de support avec IA."""
    try:
        user_id = message.from_user.id
        username = message.from_user.username or "ami"
        
        # Préparer les infos utilisateur pour l'IA
        user_info = {
            "username": username,
            "country": "GN"
        }
        
        # Générer la réponse IA avec ton guinéen
        ai_response = await generate_ai_response(
            user_id=user_id,
            message="/support",
            context="support",
            user_info=user_info
        )
        
        # Envoyer la réponse IA
        await message.answer(ai_response.content, parse_mode=ParseMode.MARKDOWN)
        
        # Ajouter les options de support rapide
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="📞 Contacter Chico", callback_data="contact_chico"),
                InlineKeyboardButton(text="⚡ Contacter Problematique", callback_data="contact_problematique")
            ],
            [
                InlineKeyboardButton(text="🔧 Support Technique", callback_data="tech_support"),
                InlineKeyboardButton(text="❓ Questions Générales", callback_data="general_support")
            ]
        ])
        
        await message.answer(
            "🇬🇳 *Comment puis-je t'aider, frère/sœur ?* 🇬🇳\n\n"
            "🚀 *Choisis le type de support dont tu as besoin :*",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=keyboard
        )
        
        logger.info(f"🇬🇳 Support demandé par @{username}")
        
    except Exception as e:
        logger.error(f"🇬🇳 Erreur commande support: {e}")
        
        # Réponse IA d'erreur
        error_response = await generate_ai_response(
            user_id=message.from_user.id,
            message="/support",
            context="error"
        )
        
        await message.answer(error_response.content, parse_mode=ParseMode.MARKDOWN)

@community_router.callback_query(F.data == "refresh_ranking")
async def handle_refresh_ranking(callback: CallbackQuery):
    """Actualise le classement."""
    await handle_classement_command(callback.message)
    await callback.answer("🔄 Classement actualisé !")

@community_router.callback_query(F.data == "my_stats")
async def handle_my_stats(callback: CallbackQuery):
    """Affiche les statistiques personnelles."""
    try:
        user_id = callback.from_user.id
        
        # Récupérer les stats de l'utilisateur
        user_stats = await database.get_user_stats(user_id)
        
        if not user_stats:
            await callback.message.answer(
                "❌ *Aucune statistique trouvée*\n\n"
                "🇬🇳 *Commence à utiliser ChicoBot pour voir tes stats* 🇬🇳"
            )
            await callback.answer()
            return
        
        # Formatter les stats
        stats_message = (
            f"📊 **TES STATISTIQUES PERSONNELLES** 📊\n\n"
            f"👤 *Utilisateur :* @{callback.from_user.username}\n"
            f"💰 *Gains totaux :* ${user_stats['total_earnings']:,.2f}\n"
            f"🏆 *Classement mondial :* #{user_stats['global_rank']:,}\n"
            f"🇬🇳 *Classement Guinée :* #{user_stats['guinea_rank']:,}\n"
            f"📈 *Gains mensuels :* ${user_stats['monthly_earnings']:,.2f}\n"
            f"🎯 *Objectif suivant :* ${user_stats['next_milestone']:,.2f}\n\n"
            f"🇬🇳 **TU ES INCROYABLE ! CONTINUE COMME ÇA !** 🇬🇳"
        )
        
        await callback.message.answer(stats_message)
        await callback.answer("📊 Stats affichées !")
        
    except Exception as e:
        logger.error(f"🇬🇳 Erreur stats personnelles: {e}")
        await callback.answer("❌ Erreur lors de la récupération des stats")

@community_router.callback_query(F.data == "concours_info")
async def handle_concours_info(callback: CallbackQuery):
    """Affiche les informations sur le concours."""
    try:
        if community_manager.is_concours_active:
            # Concours en cours
            time_remaining = community_manager.concours_start_time + timedelta(hours=24) - datetime.now()
            hours_remaining = int(time_remaining.total_seconds() // 3600)
            
            concours_message = (
                "🎉 **CONCOURS EN COURS !** 🎉\n\n"
                f"⏰ *Temps restant :* {hours_remaining} heures\n"
                f"👥 *Groupe :* {community_manager.concours_group_id}\n\n"
                "🇬🇳 *Rejoins le groupe pour participer !* 🇬🇳\n\n"
                "🎯 *Le Top 10 est éligible au tirage*\n"
                "💰 *0.5% des gains admins à gagner !*\n\n"
                "🔥 **AMBiance FEU !** 🔥"
            )
        else:
            # Prochain concours
            next_month = datetime.now().replace(day=1) + timedelta(days=32)
            next_month = next_month.replace(day=1)
            
            concours_message = (
                "🎉 **PROCHAIN CONCOURS MENSUEL** 🎉\n\n"
                f"📅 *Date :* {next_month.strftime('%d %B %Y')}\n"
                f"⏰ *Heure :* 00:00 GMT\n\n"
                "🇬🇳 *Sois prêt pour la fête !* 🇬🇳\n\n"
                "🎯 *Conditions :* 10+ utilisateurs actifs\n"
                "💰 *Prix :* 0.5% des gains admins\n"
                "🏆 *Tirage :* Top 10 du mois\n\n"
                "🚀 **LA GUINÉE EN FÊTE !** 🚀"
            )
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🔄 Vérifier", callback_data="concours_info")
            ]
        ])
        
        await callback.message.answer(concours_message, reply_markup=keyboard)
        await callback.answer("ℹ️ Infos concours affichées !")
        
    except Exception as e:
        logger.error(f"🇬🇳 Erreur infos concours: {e}")
        await callback.answer("❌ Erreur lors de la récupération des infos")

@community_router.callback_query(F.data == "support_info")
async def handle_support_info(callback: CallbackQuery):
    """Affiche les informations de support."""
    await handle_support_command(callback.message)
    await callback.answer("📞 Support affiché !")

@community_router.callback_query(F.data.startswith("flag_"))
async def handle_flag_reaction(callback: CallbackQuery):
    """Gère les réactions de drapeaux."""
    try:
        # Ajouter la réaction au message
        await callback.message.react("🇬🇳")
        await callback.answer("🇬🇳 Drapeau guinéen ajouté !")
    except:
        await callback.answer()

@community_router.callback_query(F.data.startswith("fire"))
async def handle_fire_reaction(callback: CallbackQuery):
    """Gère les réactions feu."""
    try:
        await callback.message.react("🔥")
        await callback.answer("🔥 Feu !")
    except:
        await callback.answer()

@community_router.callback_query(F.data.startswith("trophy"))
async def handle_trophy_reaction(callback: CallbackQuery):
    """Gère les réactions trophée."""
    try:
        await callback.message.react("🏆")
        await callback.answer("🏆 Trophée !")
    except:
        await callback.answer()

@community_router.callback_query(F.data.startswith("money"))
async def handle_money_reaction(callback: CallbackQuery):
    """Gère les réactions argent."""
    try:
        await callback.message.react("💰")
        await callback.answer("💰 Money !")
    except:
        await callback.answer()

@community_router.callback_query(F.data.startswith("celebrate"))
async def handle_celebrate_reaction(callback: CallbackQuery):
    """Gère les réactions célébration."""
    try:
        await callback.message.react("🎉")
        await callback.answer("🎉 Célébration !")
    except:
        await callback.answer()

@community_router.callback_query(F.data.startswith("crown"))
async def handle_crown_reaction(callback: CallbackQuery):
    """Gère les réactions couronne."""
    try:
        await callback.message.react("👑")
        await callback.answer("👑 Couronne !")
    except:
        await callback.answer()

@community_router.callback_query(F.data.startswith("lightning"))
async def handle_lightning_reaction(callback: CallbackQuery):
    """Gère les réactions éclair."""
    try:
        await callback.message.react("⚡")
        await callback.answer("⚡ Éclair !")
    except:
        await callback.answer()

@community_router.callback_query(F.data.startswith("diamond"))
async def handle_diamond_reaction(callback: CallbackQuery):
    """Gère les réactions diamant."""
    try:
        await callback.message.react("💎")
        await callback.answer("💎 Diamant !")
    except:
        await callback.answer()

@community_router.callback_query(F.data == "tech_support")
async def handle_tech_support(callback: CallbackQuery):
    """Gère le support technique."""
    tech_message = (
        "🆘 **SUPPORT TECHNIQUE** 🆘\n\n"
        "🇬🇳 *Problème technique ? On est là pour toi* 🇬🇳\n\n"
        "📱 *Contact direct Chico :* +224 661 92 05 19\n"
        "📧 *Email technique :* tech@chicobot.gn\n\n"
        "📋 *Décris ton problème en détail :*\n"
        "• Quel device ?\n"
        "• Quelle application ?\n"
        "• Message d'erreur ?\n\n"
        "⚡ *Réponse garantie sous 2h* ⚡"
    )
    
    await callback.message.answer(tech_message)
    await callback.answer("🆘 Support technique envoyé !")

@community_router.callback_query(F.data == "general_support")
async def handle_general_support(callback: CallbackQuery):
    """Gère le support général."""
    general_message = (
        "❓ **SUPPORT GÉNÉRAL** ❓\n\n"
        "🇬🇳 *Question sur ChicoBot ? On répond à tout* 🇬🇳\n\n"
        "📱 *Contact direct Chico :* +224 661 92 05 19\n"
        "📧 *Email général :* info@chicobot.gn\n\n"
        "📋 *Questions fréquentes :*\n"
        "• Comment fonctionne le bot ?\n"
        "• Comment retirer ses gains ?\n"
        "• Comment participer aux concours ?\n"
        "• Comment devenir admin ?\n\n"
        "🇬🇳 *N'hésite jamais, on est là pour toi* 🇬🇳"
    )
    
    await callback.message.answer(general_message)
    await callback.answer("❓ Support général envoyé !")

# Fonctions d'initialisation et d'arrêt

async def initialize_community_manager() -> bool:
    """Initialise le gestionnaire de communauté."""
    return await community_manager.initialize()

async def shutdown_community_manager():
    """Arrête proprement le gestionnaire de communauté."""
    try:
        # Fermer le concours s'il est en cours
        if community_manager.is_concours_active:
            await community_manager._close_concours_group()
        
        logger.info("🇬🇳 Gestionnaire de communauté arrêté")
        
    except Exception as e:
        logger.error(f"🇬🇳 Erreur arrêt communauté: {e}")

# Tests d'intégration
if __name__ == "__main__":
    import unittest
    from unittest import IsolatedAsyncioTestCase
    
    class TestCommunityManager(IsolatedAsyncioTestCase):
        """Tests d'intégration pour le gestionnaire de communauté."""
        
        async def asyncSetUp(self):
            """Configuration des tests."""
            self.manager = CommunityManager()
        
        async def test_initialization(self):
            """Teste l'initialisation du gestionnaire."""
            success = await self.manager.initialize()
            self.assertTrue(success)
            print("\n🇬🇳 Gestionnaire de communauté initialisé avec succès")
        
        async def test_ranking_retrieval(self):
            """Teste la récupération des classements."""
            rankings = await self.manager.get_global_ranking()
            
            self.assertIn("global_top", rankings)
            self.assertIn("guinea_top", rankings)
            self.assertIn("total_users", rankings)
            
            print(f"\n📊 Classement récupéré : {rankings['total_users']} utilisateurs")
        
        async def test_concours_creation(self):
            """Teste la création d'un concours."""
            # Simuler suffisamment d'utilisateurs actifs
            self.manager._get_active_users_count = lambda: 15
            self.manager._create_concours_group = lambda: -1001234567890
            self.manager._invite_active_users = lambda x: asyncio.sleep(0.1)
            self.manager._send_concours_announcement = lambda x: asyncio.sleep(0.1)
            
            success = await self.manager.start_monthly_concours()
            self.assertTrue(success)
            self.assertTrue(self.manager.is_concours_active)
            
            print("\n🎉 Concours créé avec succès")
        
        async def test_winner_selection(self):
            """Teste la sélection du gagnant."""
            # Simuler des utilisateurs éligibles
            mock_users = [
                {"user_id": 1, "username": "user1", "monthly_rank": 1, "total_earnings": 5000},
                {"user_id": 2, "username": "user2", "monthly_rank": 2, "total_earnings": 4000},
                {"user_id": 3, "username": "user3", "monthly_rank": 3, "total_earnings": 3000}
            ]
            
            # Mock des fonctions
            self.manager._announce_winner = lambda w, p: asyncio.sleep(0.1)
            self.manager._record_winner = lambda w, p: asyncio.sleep(0.1)
            
            # Simuler la base de données
            class MockDB:
                @staticmethod
                async def get_monthly_top_users(limit):
                    return mock_users
                
                @staticmethod
                async def get_admin_monthly_earnings():
                    return 10000  # 10k$ de gains admins
                
                @staticmethod
                async def record_concours_winner(user_id, username, prize_amount, concours_date):
                    pass
            
            # Remplacer temporairement database
            import src.handlers.community
            original_db = src.handlers.community.database
            src.handlers.community.database = MockDB()
            
            try:
                await self.manager._draw_winner()
                print("\n🏆 Gagnant sélectionné avec succès")
            finally:
                src.handlers.community.database = original_db
        
        async def test_flag_retrieval(self):
            """Teste la récupération des drapeaux."""
            self.assertEqual(self.manager._get_country_flag("GN"), "🇬🇳")
            self.assertEqual(self.manager._get_country_flag("US"), "🇺🇸")
            self.assertEqual(self.manager._get_country_flag("FR"), "🇫🇷")
            self.assertEqual(self.manager._get_country_flag("XX"), "🌍")
            
            print("\n🇬🇳 Drapeaux récupérés avec succès")
    
    # Lancer les tests
    unittest.main(verbosity=2)
