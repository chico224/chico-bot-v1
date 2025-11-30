"""
Handlers Chico - Toutes les commandes du bot avec la voix de Chico
Chaque réponse passe par le moteur de personnalité Chico
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from ..core.chico_personality import chico_respond
from ..core.database import DatabaseManager
from ..core.logging_setup import setup_logging

logger = setup_logging("chico_handlers")

class ChicoHandlers:
    """
    Handlers pour toutes les commandes du bot
    CHAQUE RÉPONSE passe par chico_respond() -> IA avec la voix de Chico
    """
    
    def __init__(self):
        self.database = DatabaseManager()
        self.logger = setup_logging("chico_handlers")
        
    async def handle_start(self, user_id: str, username: str = None) -> str:
        """Handler pour /start"""
        
        # Enregistrer l'utilisateur
        await self.database.register_user(user_id, username)
        
        # Contexte pour personnalisation
        context = {
            "first_time": True,
            "username": username,
            "user_level": "Débutant 🌱"
        }
        
        # Générer la réponse avec la voix de Chico
        response = await chico_respond("/start", user_id, context)
        
        return response
        
    async def handle_help(self, user_id: str) -> str:
        """Handler pour /help"""
        
        context = await self._get_user_context(user_id)
        response = await chico_respond("/help", user_id, context)
        
        return response
        
    async def handle_balance(self, user_id: str) -> str:
        """Handler pour /balance"""
        
        # Récupérer le solde
        balance = await self.database.get_user_balance(user_id)
        
        # Contexte personnalisé
        context = await self._get_user_context(user_id)
        context["current_balance"] = balance
        
        # Message personnalisé selon le solde
        if balance >= 2000:
            user_message = f"Mon solde est de {balance:.2f} USDT, je suis au niveau légendaire !"
        elif balance >= 1000:
            user_message = f"Mon solde est de {balance:.2f} USDT, je suis avancé !"
        elif balance >= 500:
            user_message = f"Mon solde est de {balance:.2f} USDT, je progresse bien !"
        elif balance > 0:
            user_message = f"Mon solde est de {balance:.2f} USDT, c'est un début !"
        else:
            user_message = "Je n'ai pas encore d'argent, comment commencer ?"
            
        response = await chico_respond(user_message, user_id, context)
        
        return response
        
    async def handle_deposit(self, user_id: str, amount: float = None) -> str:
        """Handler pour /deposit"""
        
        context = await self._get_user_context(user_id)
        
        if amount is None:
            # Demander le montant
            user_message = "Je veux déposer de l'argent, comment faire ?"
        else:
            # Simuler le dépôt
            current_balance = await self.database.get_user_balance(user_id)
            new_balance = current_balance + amount
            await self.database.update_user_balance(user_id, new_balance)
            
            context["deposit_amount"] = amount
            context["new_balance"] = new_balance
            
            user_message = f"Je viens de déposer {amount:.2f} USDT, mon nouveau solde est {new_balance:.2f} USDT !"
            
        response = await chico_respond(user_message, user_id, context)
        
        return response
        
    async def handle_trading(self, user_id: str, action: str = "status") -> str:
        """Handler pour /trading"""
        
        context = await self._get_user_context(user_id)
        
        # Vérifier si le trading est activé
        balance = await self.database.get_user_balance(user_id)
        
        if balance < 1000:
            user_message = "Je veux faire du trading mais j'ai moins de 1000 USDT"
        elif action == "start":
            user_message = "Je veux lancer le trading automatique maintenant !"
        elif action == "stop":
            user_message = "Je veux arrêter le trading pour le moment"
        else:
            user_message = "Comment marche le trading automatique ?"
            
        response = await chico_respond(user_message, user_id, context)
        
        return response
        
    async def handle_withdraw(self, user_id: str, amount: float = None) -> str:
        """Handler pour /withdraw"""
        
        context = await self._get_user_context(user_id)
        balance = await self.database.get_user_balance(user_id)
        
        if amount is None:
            user_message = "Je veux retirer de l'argent, comment faire ?"
        elif amount > balance:
            user_message = f"Je veux retirer {amount:.2f} USDT mais je n'ai que {balance:.2f} USDT"
        else:
            # Simuler le retrait
            new_balance = balance - amount
            await self.database.update_user_balance(user_id, new_balance)
            
            context["withdraw_amount"] = amount
            context["new_balance"] = new_balance
            
            user_message = f"Je viens de retirer {amount:.2f} USDT, il me reste {new_balance:.2f} USDT"
            
        response = await chico_respond(user_message, user_id, context)
        
        return response
        
    async def handle_stats(self, user_id: str) -> str:
        """Handler pour /stats"""
        
        context = await self._get_user_context(user_id)
        
        # Récupérer les statistiques
        stats = await self.database.get_user_stats(user_id)
        
        context.update(stats)
        
        if stats.get("total_trades", 0) > 0:
            user_message = f"Montre-moi mes stats : {stats.get('total_trades')} trades, {stats.get('win_rate', 0):.1f}% de win rate"
        else:
            user_message = "Je n'ai pas encore de stats, comment commencer ?"
            
        response = await chico_respond(user_message, user_id, context)
        
        return response
        
    async def handle_classement(self, user_id: str) -> str:
        """Handler pour /classement"""
        
        context = await self._get_user_context(user_id)
        
        # Récupérer le classement
        rankings = await self.database.get_top_users(10)
        
        # Position de l'utilisateur
        user_rank = await self.database.get_user_rank(user_id)
        
        context["rankings"] = rankings[:5]  # Top 5 pour le contexte
        context["user_rank"] = user_rank
        
        if user_rank <= 10:
            user_message = f"Je suis {user_rank}ème au classement ! Montre-moi le top !"
        else:
            user_message = "Je veux voir le classement des meilleurs traders"
            
        response = await chico_respond(user_message, user_id, context)
        
        return response
        
    async def handle_support(self, user_id: str, message: str = None) -> str:
        """Handler pour /support"""
        
        context = await self._get_user_context(user_id)
        
        if message is None:
            user_message = "J'ai besoin d'aide, je peux parler à qui ?"
        else:
            # Enregistrer la demande de support
            await self.database.create_support_ticket(user_id, message)
            
            context["support_message"] = message
            user_message = f"J'ai un problème : {message}"
            
        response = await chico_respond(user_message, user_id, context)
        
        return response
        
    async def handle_multitask_status(self, user_id: str) -> str:
        """Handler pour le statut multitâche"""
        
        context = await self._get_user_context(user_id)
        
        try:
            # Récupérer le statut du système multitâche
            from ..core.multitask_integration import get_orchestrator
            orchestrator = get_orchestrator(self.database)
            
            if orchestrator and orchestrator.running:
                dashboard = await orchestrator.get_dashboard_data()
                
                context.update({
                    "active_tasks": dashboard.get("active_tasks", 0),
                    "total_tasks": dashboard.get("total_tasks", 0),
                    "uptime": dashboard.get("orchestrator_uptime", 0)
                })
                
                user_message = f"Montre-moi le statut des tâches : {dashboard.get('active_tasks', 0)} actives sur {dashboard.get('total_tasks', 0)}"
            else:
                user_message = "Pourquoi les tâches automatiques ne tournent pas ?"
                
        except Exception as e:
            self.logger.error(f"Erreur multitâche status: {e}")
            user_message = "Je veux comprendre comment marchent les tâches automatiques"
            
        response = await chico_respond(user_message, user_id, context)
        
        return response
        
    async def handle_general_message(self, user_id: str, message: str) -> str:
        """Handler pour les messages généraux (non commandes)"""
        
        context = await self._get_user_context(user_id)
        
        # Ajouter des informations contextuelles
        context["is_general_message"] = True
        context["message_length"] = len(message)
        
        # Générer la réponse avec la voix de Chico
        response = await chico_respond(message, user_id, context)
        
        return response
        
    async def _get_user_context(self, user_id: str) -> Dict[str, Any]:
        """Récupérer le contexte complet de l'utilisateur"""
        
        try:
            # Solde
            balance = await self.database.get_user_balance(user_id)
            
            # Statistiques
            stats = await self.database.get_user_stats(user_id)
            
            # Niveau selon solde
            if balance >= 2000:
                level = "Légendaire 🔥"
            elif balance >= 1000:
                level = "Avancé 🚀"
            elif balance >= 500:
                level = "Intermédiaire ⚡"
            else:
                level = "Débutant 🌱"
                
            # Tâches actives (si disponible)
            active_tasks = 0
            try:
                from ..core.multitask_integration import get_orchestrator
                orchestrator = get_orchestrator(self.database)
                if orchestrator and orchestrator.running:
                    dashboard = await orchestrator.get_dashboard_data()
                    active_tasks = dashboard.get("active_tasks", 0)
            except:
                pass
                
            return {
                "balance": balance,
                "user_level": level,
                "active_tasks": active_tasks,
                "total_trades": stats.get("total_trades", 0),
                "win_rate": stats.get("win_rate", 0),
                "total_profit": stats.get("total_profit", 0),
                "user_id": user_id
            }
            
        except Exception as e:
            self.logger.error(f"Erreur contexte utilisateur: {e}")
            return {"user_id": user_id}

# Singleton global
_handlers_instance: Optional[ChicoHandlers] = None

def get_chico_handlers() -> ChicoHandlers:
    """Getter pour le singleton handlers"""
    global _handlers_instance
    if _handlers_instance is None:
        _handlers_instance = ChicoHandlers()
    return _handlers_instance

# Export pour usage externe
__all__ = [
    'ChicoHandlers',
    'get_chico_handlers'
]
