"""
Système Admin ChicoBot - Gestion Ultra-Sécurisée des Administrateurs.

Fonctionnalités principales :
- Quiz d'authentification sécurisé à 3 questions
- Gestion des admins avec limite de 3 admins maximum
- Répartition automatique de 2% des gains mensuels des utilisateurs
- Stockage sécurisé en base de données
- Messages de confirmation et notifications admin

🇬🇳 Système admin niveau sécurité militaire 🇬🇳
"""

import asyncio
import hashlib
import json
import logging
import os
import secrets
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import aiohttp
import numpy as np
from aiogram import Router, types
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, ReplyKeyboardRemove

from config.settings import settings
from core.database import database
from core.logging_setup import get_logger
from core.security import WalletSecurityManager

# Configuration du logger
logger = get_logger(__name__)

# Router pour les commandes admin
admin_router = Router()

# 🇬🇳 Configuration du Système Admin 🇬🇳
MAX_ADMINS = 3
ADMIN_COMMISSION_RATE = 0.02  # 2% des gains mensuels
ADMIN_QUIZ_TIMEOUT = 300  # 5 minutes pour répondre au quiz
ADMIN_SESSION_TIMEOUT = 3600  # 1 heure de session admin

# 🇬🇳 Réponses du Quiz Admin (stockées hashées) 🇬🇳
# Question 1: "Quel est le nom de ta mère ?"
MOTHER_NAME_HASH = hashlib.sha256("Laouratou sow".lower().encode()).hexdigest()

# Question 2: "Quel est le nom de ton père ?" 
FATHER_NAME_HASHES = [
    hashlib.sha256("Ibrahime sorry sow".lower().encode()).hexdigest(),
    hashlib.sha256("Oumar barry".lower().encode()).hexdigest()
]

# Question 3: "Quel est ton but dans la vie ?"
LIFE_GOAL_HASH = hashlib.sha256("rendre fière la famille".lower().encode()).hexdigest()

# 🇬🇳 Questions du Quiz Admin 🇬🇳
ADMIN_QUESTIONS = [
    {
        "id": 1,
        "question": "🇬🇳 *Question 1/3* 🇬🇳\n\nQuel est le nom de ta mère ?",
        "hint": "Réponse sensible à la casse",
        "expected_hash": MOTHER_NAME_HASH
    },
    {
        "id": 2,
        "question": "🇬🇳 *Question 2/3* 🇬🇳\n\nQuel est le nom de ton père ?",
        "hint": "Plusieurs réponses possibles",
        "expected_hashes": FATHER_NAME_HASHES
    },
    {
        "id": 3,
        "question": "🇬🇳 *Question 3/3* 🇬🇳\n\nQuel est ton but dans la vie ?",
        "hint": "Une phrase inspirante",
        "expected_hash": LIFE_GOAL_HASH
    }
]

# États FSM pour le quiz admin
class AdminQuizStates(StatesGroup):
    answering_question_1 = State()
    answering_question_2 = State()
    answering_question_3 = State()
    quiz_completed = State()

class AdminSystem:
    """Système de gestion des administrateurs ChicoBot."""
    
    def __init__(self):
        self.current_admin_sessions = {}  # Sessions admin actives
        self.pending_quizzes = {}  # Quiz en cours
        self.admin_stats = {}  # Statistiques des admins
        self.is_initialized = False
        
    async def initialize(self) -> bool:
        """Initialise le système admin."""
        try:
            logger.info("🇬🇳 Initialisation du système admin ChicoBot... 🇬🇳")
            
            # Charger les admins existants depuis la base de données
            await self._load_existing_admins()
            
            # Initialiser les statistiques
            await self._initialize_stats()
            
            # Démarrer les tâches de fond
            asyncio.create_task(self._admin_monitoring())
            asyncio.create_task(self._commission_calculator())
            
            self.is_initialized = True
            logger.info("🇬🇳 Système admin initialisé avec succès ! 🇬🇳")
            
            return True
            
        except Exception as e:
            logger.error(f"🇬🇳 Erreur initialisation système admin: {e}")
            return False
    
    async def _load_existing_admins(self):
        """Charge les administrateurs existants depuis la base de données."""
        try:
            # Récupérer tous les admins depuis la base de données
            admins_data = await database.get_all_admins()
            
            for admin_data in admins_data:
                user_id = admin_data.get("user_id")
                username = admin_data.get("username")
                joined_at = admin_data.get("joined_at")
                is_active = admin_data.get("is_active", True)
                
                if is_active:
                    self.current_admin_sessions[user_id] = {
                        "username": username,
                        "joined_at": joined_at,
                        "last_activity": datetime.now(),
                        "session_active": False
                    }
            
            logger.info(f"🇬🇳 {len(self.current_admin_sessions)} admins chargés")
            
        except Exception as e:
            logger.error(f"🇬🇳 Erreur chargement admins: {e}")
    
    async def _initialize_stats(self):
        """Initialise les statistiques des admins."""
        try:
            for admin_id in self.current_admin_sessions:
                self.admin_stats[admin_id] = {
                    "total_commissions": 0.0,
                    "monthly_commissions": 0.0,
                    "last_commission_date": None,
                    "total_users_managed": 0,
                    "active_since": self.current_admin_sessions[admin_id]["joined_at"]
                }
            
            logger.info("🇬🇳 Statistiques admin initialisées")
            
        except Exception as e:
            logger.error(f"🇬🇳 Erreur initialisation stats: {e}")
    
    async def start_admin_quiz(self, user_id: int, username: str) -> Dict[str, Any]:
        """Démarre le quiz d'authentification admin."""
        try:
            # Vérifier si l'utilisateur n'est pas déjà admin
            if user_id in self.current_admin_sessions:
                return {
                    "success": False,
                    "message": "Tu es déjà administrateur !",
                    "is_already_admin": True
                }
            
            # Vérifier si on a atteint la limite d'admins
            if len(self.current_admin_sessions) >= MAX_ADMINS:
                return {
                    "success": False,
                    "message": f"Limite de {MAX_ADMINS} admins atteinte !",
                    "admin_limit_reached": True
                }
            
            # Vérifier si un quiz est déjà en cours pour cet utilisateur
            if user_id in self.pending_quizzes:
                return {
                    "success": False,
                    "message": "Quiz déjà en cours !",
                    "quiz_in_progress": True
                }
            
            # Initialiser le quiz
            quiz_data = {
                "user_id": user_id,
                "username": username,
                "started_at": datetime.now(),
                "current_question": 1,
                "answers": {},
                "expires_at": datetime.now() + timedelta(seconds=ADMIN_QUIZ_TIMEOUT)
            }
            
            self.pending_quizzes[user_id] = quiz_data
            
            logger.info(f"🇬🇳 Quiz admin démarré pour {username} ({user_id})")
            
            return {
                "success": True,
                "message": "Quiz admin démarré !",
                "first_question": ADMIN_QUESTIONS[0]["question"],
                "quiz_id": user_id,
                "timeout": ADMIN_QUIZ_TIMEOUT
            }
            
        except Exception as e:
            logger.error(f"🇬🇳 Erreur démarrage quiz admin: {e}")
            return {"success": False, "message": "Erreur technique"}
    
    async def submit_quiz_answer(self, user_id: int, question_id: int, answer: str) -> Dict[str, Any]:
        """Soumet une réponse au quiz admin."""
        try:
            # Vérifier si le quiz existe et n'est pas expiré
            if user_id not in self.pending_quizzes:
                return {
                    "success": False,
                    "message": "Quiz non trouvé ou expiré",
                    "quiz_not_found": True
                }
            
            quiz_data = self.pending_quizzes[user_id]
            
            # Vérifier l'expiration
            if datetime.now() > quiz_data["expires_at"]:
                del self.pending_quizzes[user_id]
                return {
                    "success": False,
                    "message": "Quiz expiré !",
                    "quiz_expired": True
                }
            
            # Vérifier si c'est la bonne question
            if quiz_data["current_question"] != question_id:
                return {
                    "success": False,
                    "message": "Question non valide",
                    "invalid_question": True
                }
            
            # Valider la réponse
            question_data = ADMIN_QUESTIONS[question_id - 1]
            answer_hash = hashlib.sha256(answer.lower().strip().encode()).hexdigest()
            
            is_correct = False
            if "expected_hash" in question_data:
                is_correct = answer_hash == question_data["expected_hash"]
            elif "expected_hashes" in question_data:
                is_correct = answer_hash in question_data["expected_hashes"]
            
            # Enregistrer la réponse
            quiz_data["answers"][question_id] = {
                "answer": answer,  # Stocker la réponse en clair pour le logging
                "answer_hash": answer_hash,  # Hash pour validation
                "is_correct": is_correct,
                "submitted_at": datetime.now()
            }
            
            if not is_correct:
                # Mauvaise réponse - supprimer le quiz
                del self.pending_quizzes[user_id]
                return {
                    "success": False,
                    "message": f"Mauvaise réponse à la question {question_id} ! Quiz terminé.",
                    "incorrect_answer": True,
                    "quiz_failed": True
                }
            
            # Bonne réponse - passer à la question suivante
            if question_id < 3:
                quiz_data["current_question"] = question_id + 1
                next_question = ADMIN_QUESTIONS[question_id]["question"]
                
                return {
                    "success": True,
                    "message": "Bonne réponse !",
                    "next_question": next_question,
                    "next_question_id": question_id + 1,
                    "progress": f"{question_id}/3"
                }
            else:
                # Quiz terminé avec succès
                await self._complete_quiz_successfully(user_id)
                
                return {
                    "success": True,
                    "message": "Quiz terminé avec succès !",
                    "quiz_completed": True,
                    "admin_granted": True
                }
            
        except Exception as e:
            logger.error(f"🇬🇳 Erreur soumission réponse quiz: {e}")
            return {"success": False, "message": "Erreur technique"}
    
    async def _complete_quiz_successfully(self, user_id: int):
        """Traite la réussite du quiz admin."""
        try:
            quiz_data = self.pending_quizzes[user_id]
            username = quiz_data["username"]
            
            # Ajouter l'utilisateur comme admin
            admin_data = {
                "user_id": user_id,
                "username": username,
                "joined_at": datetime.now(),
                "is_active": True
            }
            
            # Sauvegarder en base de données
            await database.add_admin(admin_data)
            
            # Ajouter aux sessions admin actives
            self.current_admin_sessions[user_id] = {
                "username": username,
                "joined_at": datetime.now(),
                "last_activity": datetime.now(),
                "session_active": True
            }
            
            # Initialiser les statistiques
            self.admin_stats[user_id] = {
                "total_commissions": 0.0,
                "monthly_commissions": 0.0,
                "last_commission_date": None,
                "total_users_managed": 0,
                "active_since": datetime.now()
            }
            
            # Supprimer le quiz
            del self.pending_quizzes[user_id]
            
            logger.info(f"🇬🇳 Nouveau admin ajouté : {username} ({user_id})")
            
        except Exception as e:
            logger.error(f"🇬🇳 Erreur complétion quiz: {e}")
    
    async def is_admin(self, user_id: int) -> bool:
        """Vérifie si un utilisateur est admin."""
        return user_id in self.current_admin_sessions
    
    async def get_admin_info(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Récupère les informations d'un admin."""
        if user_id not in self.current_admin_sessions:
            return None
        
        admin_info = self.current_admin_sessions[user_id].copy()
        admin_info.update(self.admin_stats.get(user_id, {}))
        return admin_info
    
    async def get_all_admins(self) -> List[Dict[str, Any]]:
        """Récupère tous les admins actifs."""
        admins_list = []
        
        for admin_id, session_data in self.current_admin_sessions.items():
            admin_info = session_data.copy()
            admin_info.update(self.admin_stats.get(admin_id, {}))
            admin_info["user_id"] = admin_id
            admins_list.append(admin_info)
        
        return admins_list
    
    async def remove_admin(self, admin_id: int, removed_by: int) -> Dict[str, Any]:
        """Supprime un admin (uniquement par un autre admin)."""
        try:
            # Vérifier que celui qui supprime est admin
            if removed_by not in self.current_admin_sessions:
                return {
                    "success": False,
                    "message": "Seul un admin peut supprimer un autre admin"
                }
            
            # Vérifier que l'admin à supprimer existe
            if admin_id not in self.current_admin_sessions:
                return {
                    "success": False,
                    "message": "Admin non trouvé"
                }
            
            # Empêcher l'auto-suppression
            if admin_id == removed_by:
                return {
                    "success": False,
                    "message": "Tu ne peux pas te supprimer toi-même"
                }
            
            # Supprimer l'admin
            admin_username = self.current_admin_sessions[admin_id]["username"]
            
            # Marquer comme inactif en base de données
            await database.update_admin_status(admin_id, False)
            
            # Supprimer des sessions actives
            del self.current_admin_sessions[admin_id]
            
            # Supprimer les statistiques
            if admin_id in self.admin_stats:
                del self.admin_stats[admin_id]
            
            logger.info(f"🇬🇳 Admin {admin_username} ({admin_id}) supprimé par {removed_by}")
            
            return {
                "success": True,
                "message": f"Admin {admin_username} supprimé avec succès"
            }
            
        except Exception as e:
            logger.error(f"🇬🇳 Erreur suppression admin: {e}")
            return {"success": False, "message": "Erreur technique"}
    
    async def calculate_monthly_commissions(self) -> Dict[str, Any]:
        """Calcule les commissions mensuelles des admins."""
        try:
            # Récupérer tous les gains du mois précédent
            previous_month = datetime.now().replace(day=1) - timedelta(days=1)
            previous_month_start = previous_month.replace(day=1)
            
            # Calculer le total des gains de tous les utilisateurs
            total_monthly_earnings = await database.get_total_monthly_earnings(previous_month_start, previous_month)
            
            if total_monthly_earnings <= 0:
                return {
                    "total_earnings": 0,
                    "commission_pool": 0,
                    "admin_count": len(self.current_admin_sessions),
                    "commissions": {}
                }
            
            # Calculer le pool de commissions (2% des gains)
            commission_pool = total_monthly_earnings * ADMIN_COMMISSION_RATE
            
            # Répartir équitablement entre les admins actifs
            active_admins = len(self.current_admin_sessions)
            
            if active_admins == 0:
                return {
                    "total_earnings": total_monthly_earnings,
                    "commission_pool": commission_pool,
                    "admin_count": 0,
                    "commissions": {}
                }
            
            commission_per_admin = commission_pool / active_admins
            
            # Distribuer les commissions
            commissions = {}
            for admin_id in self.current_admin_sessions:
                commissions[admin_id] = commission_per_admin
                
                # Mettre à jour les statistiques
                if admin_id in self.admin_stats:
                    self.admin_stats[admin_id]["monthly_commissions"] = commission_per_admin
                    self.admin_stats[admin_id]["total_commissions"] += commission_per_admin
                    self.admin_stats[admin_id]["last_commission_date"] = datetime.now()
                
                # Enregistrer la commission en base de données
                await database.add_admin_commission(admin_id, commission_per_admin, previous_month)
            
            logger.info(f"🇬🇳 Commissions mensuelles calculées : {commission_pool:.2f}$ pour {active_admins} admins")
            
            return {
                "total_earnings": total_monthly_earnings,
                "commission_pool": commission_pool,
                "admin_count": active_admins,
                "commission_per_admin": commission_per_admin,
                "commissions": commissions
            }
            
        except Exception as e:
            logger.error(f"🇬🇳 Erreur calcul commissions: {e}")
            return {"error": str(e)}
    
    async def get_admin_dashboard(self, admin_id: int) -> Dict[str, Any]:
        """Génère le dashboard admin."""
        try:
            if admin_id not in self.current_admin_sessions:
                return {"error": "Non autorisé"}
            
            admin_stats = self.admin_stats.get(admin_id, {})
            all_admins = await self.get_all_admins()
            
            # Statistiques générales
            total_users = await database.get_total_users_count()
            active_users = await database.get_active_users_count()
            total_earnings = await database.get_total_earnings()
            monthly_earnings = await database.get_current_month_earnings()
            
            dashboard = {
                "admin_info": {
                    "user_id": admin_id,
                    "username": self.current_admin_sessions[admin_id]["username"],
                    "joined_at": self.current_admin_sessions[admin_id]["joined_at"],
                    "total_commissions": admin_stats.get("total_commissions", 0),
                    "monthly_commissions": admin_stats.get("monthly_commissions", 0),
                    "last_commission": admin_stats.get("last_commission_date")
                },
                "system_stats": {
                    "total_users": total_users,
                    "active_users": active_users,
                    "total_earnings": total_earnings,
                    "monthly_earnings": monthly_earnings,
                    "admin_count": len(all_admins)
                },
                "all_admins": all_admins,
                "commission_rate": ADMIN_COMMISSION_RATE * 100
            }
            
            return dashboard
            
        except Exception as e:
            logger.error(f"🇬🇳 Erreur dashboard admin: {e}")
            return {"error": str(e)}
    
    async def _admin_monitoring(self):
        """Surveillance des sessions admin."""
        logger.info("🇬🇳 Démarrage monitoring admin...")
        
        while True:
            try:
                current_time = datetime.now()
                expired_sessions = []
                
                # Vérifier les sessions expirées
                for admin_id, session_data in self.current_admin_sessions.items():
                    if session_data.get("session_active", False):
                        last_activity = session_data["last_activity"]
                        if current_time - last_activity > timedelta(seconds=ADMIN_SESSION_TIMEOUT):
                            session_data["session_active"] = False
                            expired_sessions.append(admin_id)
                
                # Nettoyer les quiz expirés
                expired_quizzes = []
                for user_id, quiz_data in self.pending_quizzes.items():
                    if current_time > quiz_data["expires_at"]:
                        expired_quizzes.append(user_id)
                
                for user_id in expired_quizzes:
                    del self.pending_quizzes[user_id]
                    logger.info(f"🇬🇳 Quiz expiré pour utilisateur {user_id}")
                
                # Pause de monitoring
                await asyncio.sleep(60)  # Vérifier toutes les minutes
                
            except Exception as e:
                logger.error(f"🇬🇳 Erreur monitoring admin: {e}")
                await asyncio.sleep(60)
    
    async def _commission_calculator(self):
        """Calculateur de commissions automatique."""
        logger.info("🇬🇳 Démarrage calculateur commissions...")
        
        while True:
            try:
                # Calculer les commissions au début de chaque mois
                current_time = datetime.now()
                
                # Exécuter le 1er de chaque mois à minuit
                if current_time.day == 1 and current_time.hour == 0:
                    await self.calculate_monthly_commissions()
                
                # Pause d'une heure
                await asyncio.sleep(3600)
                
            except Exception as e:
                logger.error(f"🇬🇳 Erreur calculateur commissions: {e}")
                await asyncio.sleep(3600)
    
    async def cleanup_expired_quizzes(self):
        """Nettoie les quiz expirés."""
        try:
            current_time = datetime.now()
            expired_quizzes = []
            
            for user_id, quiz_data in self.pending_quizzes.items():
                if current_time > quiz_data["expires_at"]:
                    expired_quizzes.append(user_id)
            
            for user_id in expired_quizzes:
                del self.pending_quizzes[user_id]
                logger.info(f"🇬🇳 Quiz expiré nettoyé pour utilisateur {user_id}")
            
            return len(expired_quizzes)
            
        except Exception as e:
            logger.error(f"🇬🇳 Erreur nettoyage quiz: {e}")
            return 0
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Récupère le statut du système admin."""
        try:
            return {
                "initialized": self.is_initialized,
                "total_admins": len(self.current_admin_sessions),
                "max_admins": MAX_ADMINS,
                "active_quizzes": len(self.pending_quizzes),
                "commission_rate": ADMIN_COMMISSION_RATE * 100,
                "admin_list": [
                    {
                        "user_id": admin_id,
                        "username": data["username"],
                        "joined_at": data["joined_at"],
                        "session_active": data.get("session_active", False)
                    }
                    for admin_id, data in self.current_admin_sessions.items()
                ]
            }
            
        except Exception as e:
            logger.error(f"🇬🇳 Erreur statut système: {e}")
            return {"error": str(e)}

# Instance globale du système admin
admin_system = AdminSystem()

# Handlers de commandes admin
@admin_router.message(Command("admin"))
async def handle_admin_command(message: Message, state: FSMContext) -> None:
    """Gère la commande /admin."""
    user_id = message.from_user.id
    username = message.from_user.username or "inconnu"
    
    logger.info(f"🇬🇳 Commande /admin reçue de {username} ({user_id})")
    
    # Vérifier si déjà admin
    if await admin_system.is_admin(user_id):
        await message.answer(
            "🇬🇳 *Tu es déjà administrateur !* 🇬🇳\n\n"
            "Utilise /dashboard pour voir ton tableau de bord admin.",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    # Démarrer le quiz
    quiz_result = await admin_system.start_admin_quiz(user_id, username)
    
    if not quiz_result["success"]:
        await message.answer(
            f"🇬🇳 *Erreur :* {quiz_result['message']} 🇬🇳",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    # Envoyer la première question
    await message.answer(
        quiz_result["first_question"],
        parse_mode=ParseMode.MARKDOWN
    )
    
    # Mettre à jour l'état FSM
    await state.set_state(AdminQuizStates.answering_question_1)

@admin_router.message(AdminQuizStates.answering_question_1)
async def handle_quiz_answer_1(message: Message, state: FSMContext) -> None:
    """Gère la réponse à la question 1."""
    user_id = message.from_user.id
    answer = message.text.strip()
    
    # Soumettre la réponse
    result = await admin_system.submit_quiz_answer(user_id, 1, answer)
    
    if result["success"]:
        if result.get("quiz_completed"):
            # Quiz terminé avec succès
            await message.answer(
                "🎉 **ADMIN CONFIRMÉ – BIENVENUE DANS LA FAMILLE DE CHICO** 🎉\n\n"
                "🇬🇳 *Félicitations !* Tu es maintenant administrateur ChicoBot ! 🇬🇳\n\n"
                "🔑 *Tes nouveaux pouvoirs :*\n"
                "• Accès au dashboard admin\n"
                "• Gestion des utilisateurs\n"
                "• 2% des gains mensuels de tous les utilisateurs\n\n"
                "🚀 *Utilise /dashboard pour commencer !*\n\n"
                "🇬🇳 *Bienvenue dans la famille !* 🇬🇳",
                parse_mode=ParseMode.MARKDOWN
            )
            await state.clear()
        else:
            # Passer à la question 2
            await message.answer(
                result["next_question"],
                parse_mode=ParseMode.MARKDOWN
            )
            await state.set_state(AdminQuizStates.answering_question_2)
    else:
        await message.answer(
            f"🇬🇳 *Erreur :* {result['message']} 🇬🇳",
            parse_mode=ParseMode.MARKDOWN
        )
        await state.clear()

@admin_router.message(AdminQuizStates.answering_question_2)
async def handle_quiz_answer_2(message: Message, state: FSMContext) -> None:
    """Gère la réponse à la question 2."""
    user_id = message.from_user.id
    answer = message.text.strip()
    
    # Soumettre la réponse
    result = await admin_system.submit_quiz_answer(user_id, 2, answer)
    
    if result["success"]:
        if result.get("quiz_completed"):
            # Quiz terminé avec succès
            await message.answer(
                "🎉 **ADMIN CONFIRMÉ – BIENVENUE DANS LA FAMILLE DE CHICO** 🎉\n\n"
                "🇬🇳 *Félicitations !* Tu es maintenant administrateur ChicoBot ! 🇬🇳\n\n"
                "🔑 *Tes nouveaux pouvoirs :*\n"
                "• Accès au dashboard admin\n"
                "• Gestion des utilisateurs\n"
                "• 2% des gains mensuels de tous les utilisateurs\n\n"
                "🚀 *Utilise /dashboard pour commencer !*\n\n"
                "🇬🇳 *Bienvenue dans la famille !* 🇬🇳",
                parse_mode=ParseMode.MARKDOWN
            )
            await state.clear()
        else:
            # Passer à la question 3
            await message.answer(
                result["next_question"],
                parse_mode=ParseMode.MARKDOWN
            )
            await state.set_state(AdminQuizStates.answering_question_3)
    else:
        await message.answer(
            f"🇬🇳 *Erreur :* {result['message']} 🇬🇳",
            parse_mode=ParseMode.MARKDOWN
        )
        await state.clear()

@admin_router.message(AdminQuizStates.answering_question_3)
async def handle_quiz_answer_3(message: Message, state: FSMContext) -> None:
    """Gère la réponse à la question 3."""
    user_id = message.from_user.id
    answer = message.text.strip()
    
    # Soumettre la réponse
    result = await admin_system.submit_quiz_answer(user_id, 3, answer)
    
    if result["success"] and result.get("quiz_completed"):
        # Quiz terminé avec succès
        await message.answer(
            "🎉 **ADMIN CONFIRMÉ – BIENVENUE DANS LA FAMILLE DE CHICO** 🎉\n\n"
            "🇬🇳 *Félicitations !* Tu es maintenant administrateur ChicoBot ! 🇬🇳\n\n"
            "🔑 *Tes nouveaux pouvoirs :*\n"
            "• Accès au dashboard admin\n"
            "• Gestion des utilisateurs\n"
            "• 2% des gains mensuels de tous les utilisateurs\n\n"
            "🚀 *Utilise /dashboard pour commencer !*\n\n"
            "🇬🇳 *Bienvenue dans la famille !* 🇬🇳",
            parse_mode=ParseMode.MARKDOWN
        )
        await state.clear()
    else:
        await message.answer(
            f"🇬🇳 *Erreur :* {result['message']} 🇬🇳",
            parse_mode=ParseMode.MARKDOWN
        )
        await state.clear()

@admin_router.message(Command("dashboard"))
async def handle_dashboard_command(message: Message) -> None:
    """Gère la commande /dashboard."""
    user_id = message.from_user.id
    
    # Vérifier si admin
    if not await admin_system.is_admin(user_id):
        await message.answer(
            "🇬🇳 *Commande réservée aux administrateurs !* 🇬🇳\n\n"
            "Utilise /admin pour devenir administrateur.",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    # Récupérer le dashboard
    dashboard = await admin_system.get_admin_dashboard(user_id)
    
    if "error" in dashboard:
        await message.answer(
            "🇬🇳 *Erreur lors du chargement du dashboard* 🇬🇳",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    # Formater le dashboard
    admin_info = dashboard["admin_info"]
    system_stats = dashboard["system_stats"]
    
    dashboard_message = (
        f"📊 **DASHBOARD ADMIN** 📊\n\n"
        f"🇬🇳 *Informations Admin* 🇬🇳\n"
        f"👤 *Nom :* {admin_info['username']}\n"
        f"📅 *Admin depuis :* {admin_info['joined_at'].strftime('%d/%m/%Y')}\n"
        f"💰 *Commissions totales :* {admin_info['total_commissions']:.2f}$\n"
        f"📈 *Commissions mois :* {admin_info['monthly_commissions']:.2f}$\n\n"
        f"📊 *Statistiques Système* 📊\n"
        f"👥 *Total utilisateurs :* {system_stats['total_users']}\n"
        f"🔥 *Utilisateurs actifs :* {system_stats['active_users']}\n"
        f"💵 *Gains totaux :* {system_stats['total_earnings']:.2f}$\n"
        f"📅 *Gains mois :* {system_stats['monthly_earnings']:.2f}$\n"
        f"👑 *Nombre d'admins :* {system_stats['admin_count']}/{MAX_ADMINS}\n"
        f"💸 *Taux commission :* {dashboard['commission_rate']:.1f}%\n\n"
        f"🇬🇳 *ChicoBot Admin System* 🇬🇳"
    )
    
    await message.answer(dashboard_message, parse_mode=ParseMode.MARKDOWN)

@admin_router.message(Command("admins"))
async def handle_admins_command(message: Message) -> None:
    """Gère la commande /admins."""
    user_id = message.from_user.id
    
    # Vérifier si admin
    if not await admin_system.is_admin(user_id):
        await message.answer(
            "🇬🇳 *Commande réservée aux administrateurs !* 🇬🇳",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    # Récupérer tous les admins
    admins = await admin_system.get_all_admins()
    
    if not admins:
        await message.answer(
            "🇬🇳 *Aucun administrateur trouvé* 🇬🇳",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    # Formater la liste des admins
    admins_message = "👑 **LISTE DES ADMINISTRATEURS** 👑\n\n"
    
    for i, admin in enumerate(admins, 1):
        joined_date = admin['joined_at'].strftime('%d/%m/%Y')
        commissions = admin.get('total_commissions', 0)
        
        admins_message += (
            f"🇬🇳 *Admin {i}* 🇬🇳\n"
            f"👤 *Nom :* {admin['username']}\n"
            f"📅 *Admin depuis :* {joined_date}\n"
            f"💰 *Commissions :* {commissions:.2f}$\n\n"
        )
    
    admins_message += f"🇬🇳 *Total :* {len(admins)}/{MAX_ADMINS} admins\n"
    
    await message.answer(admins_message, parse_mode=ParseMode.MARKDOWN)

@admin_router.message(Command("system"))
async def handle_system_command(message: Message) -> None:
    """Gère la commande /system."""
    user_id = message.from_user.id
    
    # Vérifier si admin
    if not await admin_system.is_admin(user_id):
        await message.answer(
            "🇬🇳 *Commande réservée aux administrateurs !* 🇬🇳",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    # Récupérer le statut du système
    status = await admin_system.get_system_status()
    
    if "error" in status:
        await message.answer(
            "🇬🇳 *Erreur lors du chargement du statut* 🇬🇳",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    # Formater le statut
    system_message = (
        f"🖥️ **STATUT SYSTÈME ADMIN** 🖥️\n\n"
        f"🇬🇳 *État du système* 🇬🇳\n"
        f"🟢 *Initialisé :* {'Oui' if status['initialized'] else 'Non'}\n"
        f"👑 *Admins actifs :* {status['total_admins']}/{status['max_admins']}\n"
        f"📝 *Quiz en cours :* {status['active_quizzes']}\n"
        f"💸 *Taux commission :* {status['commission_rate']:.1f}%\n\n"
        f"👥 *Liste des admins* 👥\n"
    )
    
    for admin in status['admin_list']:
        status_icon = "🟢" if admin['session_active'] else "🔴"
        system_message += (
            f"{status_icon} *{admin['username']}* (ID: {admin['user_id']})\n"
        )
    
    system_message += f"\n🇬🇳 *Système admin ChicoBot opérationnel* 🇬🇳"
    
    await message.answer(system_message, parse_mode=ParseMode.MARKDOWN)

# Tests d'intégration
if __name__ == "__main__":
    import unittest
    from unittest import IsolatedAsyncioTestCase
    
    class TestAdminSystem(IsolatedAsyncioTestCase):
        """Tests d'intégration pour le système admin."""
        
        async def asyncSetUp(self):
            """Configuration des tests."""
            self.admin_system = AdminSystem()
            await self.admin_system.initialize()
        
        async def test_system_initialization(self):
            """Teste l'initialisation du système admin."""
            self.assertTrue(self.admin_system.is_initialized)
            self.assertEqual(MAX_ADMINS, 3)
            self.assertEqual(ADMIN_COMMISSION_RATE, 0.02)
            
            print("\n🇬🇳 Système admin initialisé")
        
        async def test_quiz_start(self):
            """Teste le démarrage du quiz admin."""
            user_id = 12345
            username = "test_user"
            
            result = await self.admin_system.start_admin_quiz(user_id, username)
            
            self.assertTrue(result["success"])
            self.assertEqual(result["quiz_id"], user_id)
            self.assertIn("first_question", result)
            
            print("\n📝 Quiz admin démarré")
        
        async def test_quiz_correct_answers(self):
            """Teste les réponses correctes au quiz."""
            user_id = 12346
            username = "test_user2"
            
            # Démarrer le quiz
            await self.admin_system.start_admin_quiz(user_id, username)
            
            # Réponse 1 - Correcte
            result1 = await self.admin_system.submit_quiz_answer(user_id, 1, "Laouratou sow")
            self.assertTrue(result1["success"])
            self.assertFalse(result1.get("quiz_completed", False))
            
            # Réponse 2 - Correcte (première option)
            result2 = await self.admin_system.submit_quiz_answer(user_id, 2, "Ibrahime sorry sow")
            self.assertTrue(result2["success"])
            self.assertFalse(result2.get("quiz_completed", False))
            
            # Réponse 3 - Correcte
            result3 = await self.admin_system.submit_quiz_answer(user_id, 3, "rendre fière la famille")
            self.assertTrue(result3["success"])
            self.assertTrue(result3.get("quiz_completed", False))
            
            # Vérifier que l'utilisateur est maintenant admin
            self.assertTrue(await self.admin_system.is_admin(user_id))
            
            print("\n✅ Quiz complété avec succès")
        
        async def test_quiz_incorrect_answers(self):
            """Teste les réponses incorrectes au quiz."""
            user_id = 12347
            username = "test_user3"
            
            # Démarrer le quiz
            await self.admin_system.start_admin_quiz(user_id, username)
            
            # Réponse 1 - Incorrecte
            result = await self.admin_system.submit_quiz_answer(user_id, 1, "mauvaise réponse")
            self.assertFalse(result["success"])
            self.assertTrue(result.get("quiz_failed", False))
            
            # Vérifier que l'utilisateur n'est pas admin
            self.assertFalse(await self.admin_system.is_admin(user_id))
            
            print("\n❌ Quiz échoué (réponse incorrecte)")
        
        async def test_quiz_case_insensitive(self):
            """Teste la sensibilité à la casse."""
            user_id = 12348
            username = "test_user4"
            
            # Démarrer le quiz
            await self.admin_system.start_admin_quiz(user_id, username)
            
            # Réponse 1 - Majuscules/minuscules mélangées
            result1 = await self.admin_system.submit_quiz_answer(user_id, 1, "LAOURATOU SOW")
            self.assertTrue(result1["success"])
            
            # Réponse 2 - Espaces supplémentaires
            result2 = await self.admin_system.submit_quiz_answer(user_id, 2, "  Oumar barry  ")
            self.assertTrue(result2["success"])
            
            # Réponse 3 - Minuscules
            result3 = await self.admin_system.submit_quiz_answer(user_id, 3, "rendre fière la famille")
            self.assertTrue(result3["success"])
            self.assertTrue(result3.get("quiz_completed", False))
            
            print("\n🔤 Sensibilité à la casse testée")
        
        async def test_admin_limit(self):
            """Teste la limite du nombre d'admins."""
            # Créer 3 admins
            admin_ids = [12349, 12350, 12351]
            
            for i, user_id in enumerate(admin_ids):
                username = f"admin_{i}"
                await self.admin_system.start_admin_quiz(user_id, username)
                
                # Répondre correctement à toutes les questions
                await self.admin_system.submit_quiz_answer(user_id, 1, "Laouratou sow")
                await self.admin_system.submit_quiz_answer(user_id, 2, "Ibrahime sorry sow")
                await self.admin_system.submit_quiz_answer(user_id, 3, "rendre fière la famille")
                
                self.assertTrue(await self.admin_system.is_admin(user_id))
            
            # Tenter d'ajouter un 4ème admin
            user_id = 12352
            result = await self.admin_system.start_admin_quiz(user_id, "too_many")
            
            self.assertFalse(result["success"])
            self.assertTrue(result.get("admin_limit_reached", False))
            
            print("\n🚫 Limite d'admins testée")
        
        async def test_admin_info(self):
            """Teste la récupération des informations admin."""
            user_id = 12353
            username = "test_admin"
            
            # Créer un admin
            await self.admin_system.start_admin_quiz(user_id, username)
            await self.admin_system.submit_quiz_answer(user_id, 1, "Laouratou sow")
            await self.admin_system.submit_quiz_answer(user_id, 2, "Oumar barry")
            await self.admin_system.submit_quiz_answer(user_id, 3, "rendre fière la famille")
            
            # Récupérer les infos
            admin_info = await self.admin_system.get_admin_info(user_id)
            
            self.assertIsNotNone(admin_info)
            self.assertEqual(admin_info["username"], username)
            self.assertIn("joined_at", admin_info)
            self.assertIn("total_commissions", admin_info)
            
            print("\n📊 Informations admin récupérées")
        
        async def test_commission_calculation(self):
            """Teste le calcul des commissions."""
            # Simuler des gains mensuels
            # (En pratique, cela utiliserait les vraies données de la base de données)
            
            # Pour le test, nous simulons le calcul
            total_earnings = 10000.0  # 10,000$ de gains mensuels
            expected_commission_pool = total_earnings * ADMIN_COMMISSION_RATE  # 200$
            
            # Créer 2 admins pour le test
            admin_ids = [12354, 12355]
            
            for user_id in admin_ids:
                username = f"commission_test_{user_id}"
                await self.admin_system.start_admin_quiz(user_id, username)
                await self.admin_system.submit_quiz_answer(user_id, 1, "Laouratou sow")
                await self.admin_system.submit_quiz_answer(user_id, 2, "Ibrahime sorry sow")
                await self.admin_system.submit_quiz_answer(user_id, 3, "rendre fière la famille")
            
            # Calculer les commissions
            commissions = await self.admin_system.calculate_monthly_commissions()
            
            self.assertEqual(commissions["admin_count"], 2)
            self.assertEqual(commissions["commission_per_admin"], expected_commission_pool / 2)
            
            print("\n💰 Calcul des commissions testé")
        
        async def test_quiz_timeout(self):
            """Teste l'expiration du quiz."""
            user_id = 12356
            username = "timeout_test"
            
            # Démarrer le quiz
            await self.admin_system.start_admin_quiz(user_id, username)
            
            # Simuler l'expiration (modifier la date d'expiration)
            if user_id in self.admin_system.pending_quizzes:
                self.admin_system.pending_quizzes[user_id]["expires_at"] = datetime.now() - timedelta(seconds=1)
            
            # Tenter de répondre après expiration
            result = await self.admin_system.submit_quiz_answer(user_id, 1, "Laouratou sow")
            
            self.assertFalse(result["success"])
            self.assertTrue(result.get("quiz_expired", False))
            
            print("\n⏰ Expiration quiz testée")
        
        async def test_system_status(self):
            """Teste la récupération du statut du système."""
            status = await self.admin_system.get_system_status()
            
            self.assertIn("initialized", status)
            self.assertIn("total_admins", status)
            self.assertIn("max_admins", status)
            self.assertIn("commission_rate", status)
            self.assertIn("admin_list", status)
            
            self.assertTrue(status["initialized"])
            self.assertEqual(status["max_admins"], MAX_ADMINS)
            self.assertEqual(status["commission_rate"], ADMIN_COMMISSION_RATE * 100)
            
            print("\n🖥️ Statut système testé")
        
        async def test_admin_dashboard(self):
            """Teste le dashboard admin."""
            user_id = 12357
            username = "dashboard_test"
            
            # Créer un admin
            await self.admin_system.start_admin_quiz(user_id, username)
            await self.admin_system.submit_quiz_answer(user_id, 1, "Laouratou sow")
            await self.admin_system.submit_quiz_answer(user_id, 2, "Oumar barry")
            await self.admin_system.submit_quiz_answer(user_id, 3, "rendre fière la famille")
            
            # Récupérer le dashboard
            dashboard = await self.admin_system.get_admin_dashboard(user_id)
            
            self.assertNotIn("error", dashboard)
            self.assertIn("admin_info", dashboard)
            self.assertIn("system_stats", dashboard)
            self.assertIn("all_admins", dashboard)
            
            admin_info = dashboard["admin_info"]
            self.assertEqual(admin_info["username"], username)
            self.assertIn("total_commissions", admin_info)
            
            print("\n📊 Dashboard admin testé")
        
        async def test_cleanup_expired_quizzes(self):
            """Teste le nettoyage des quiz expirés."""
            # Créer quelques quiz
            user_ids = [12358, 12359, 12360]
            
            for user_id in user_ids:
                await self.admin_system.start_admin_quiz(user_id, f"cleanup_test_{user_id}")
            
            # Simuler l'expiration de certains quiz
            for user_id in user_ids[:2]:
                if user_id in self.admin_system.pending_quizzes:
                    self.admin_system.pending_quizzes[user_id]["expires_at"] = datetime.now() - timedelta(seconds=1)
            
            # Nettoyer
            cleaned_count = await self.admin_system.cleanup_expired_quizzes()
            
            self.assertEqual(cleaned_count, 2)
            self.assertEqual(len(self.admin_system.pending_quizzes), 1)
            
            print("\n🧹 Nettoyage quiz testé")
    
    # Exécuter les tests
    unittest.main()
