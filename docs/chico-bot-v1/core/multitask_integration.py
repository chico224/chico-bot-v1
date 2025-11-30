"""
Integration Multitâche - Point d'entrée principal pour le bot
Connecte le TaskMaster avec le bot principal et gère l'activation automatique
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from .task_manager import get_taskmaster, taskmaster_context
from .task_manager_integration import get_integration
from .database import DatabaseManager
from .logging_setup import setup_logging

logger = setup_logging("multitask_integration")

class MultitaskOrchestrator:
    """
    Orchestrateur principal - Gère toutes les tâches simultanées
    Architecture Two Sigma level - Performance maximale
    """
    
    def __init__(self, database: DatabaseManager):
        self.database = database
        self.taskmaster = get_taskmaster(database)
        self.integration = get_integration(database)
        self.running = False
        self.start_time = datetime.now()
        
        # État des paliers
        self.thresholds = {
            500: {"unlocked": False, "task": "rwa_monitor", "message": "RWA Monitoring débloqué !"},
            1000: {"unlocked": False, "task": "trading_bot", "message": "Trading Bot débloqué !"},
            2000: {"unlocked": False, "task": "investment_engine", "message": "Investment Engine débloqué !"}
        }
        
    async def initialize(self):
        """Initialisation de toutes les tâches"""
        logger.info("🚀 Initialisation Orchestrateur Multitâche...")
        
        # Enregistrer toutes les tâches
        await self.integration.register_all_tasks()
        
        # Bounty hunter est toujours actif (priorité critique)
        await self.taskmaster.enable_task("bounty_hunter")
        logger.info("✅ Bounty Hunter activé (toujours actif)")
        
        # Vérifier le solde actuel pour débloquer les autres tâches
        current_balance = await self.database.get_user_balance()
        await self.check_and_unlock_tasks(current_balance)
        
        logger.info("🎯 Orchestrateur initialisé avec succès")
        
    async def check_and_unlock_tasks(self, current_balance: float):
        """Vérification et déblocage des tâches selon le solde"""
        
        for threshold_amount, threshold_info in self.thresholds.items():
            if not threshold_info["unlocked"] and current_balance >= threshold_amount:
                await self.unlock_task(threshold_amount, threshold_info)
                
    async def unlock_task(self, threshold: int, threshold_info: Dict[str, Any]):
        """Déblocage d'une nouvelle tâche avec message légendaire"""
        
        task_name = threshold_info["task"]
        
        try:
            # Activer la tâche
            message = await self.taskmaster.enable_task(task_name)
            
            # Marquer comme débloqué
            self.thresholds[threshold]["unlocked"] = True
            
            # Log spécial
            logger.info("="*60)
            logger.info(f"🔥 PALIER ${threshold} ATTEINT !")
            logger.info(f"✨ {threshold_info['message']}")
            logger.info(f"🚀 Tâche {task_name} maintenant active 24/7")
            logger.info(f"💰 Toutes les tâches continuent de tourner en parallèle")
            logger.info("🇬🇳 LA GUINÉE NE DORT JAMAIS !")
            logger.info("="*60)
            
            # Envoyer notification (si système de notifications disponible)
            await self.send_notification(message)
            
        except Exception as e:
            logger.error(f"Erreur déblocage tâche {task_name}: {e}")
            
    async def send_notification(self, message: str):
        """Envoi de notification (à adapter selon votre système)"""
        try:
            # Placeholder pour système de notifications
            # Pourrait envoyer via Discord, Telegram, email, etc.
            logger.info(f"📢 Notification: {message}")
            
            # Exemple avec webhook Discord (si configuré)
            # await self.send_discord_notification(message)
            
        except Exception as e:
            logger.error(f"Erreur notification: {e}")
            
    async def start_all_tasks(self):
        """Démarrage de toutes les tâches actives"""
        self.running = True
        
        logger.info("🚀 DÉMARRAGE MULTITÂCHE ULTIME")
        logger.info("📊 Toutes les tâches actives tourneront 24/7 en parallèle")
        
        # Démarrer le TaskMaster (gère toutes les tâches)
        await self.taskmaster.start()
        
    async def stop_all_tasks(self):
        """Arrêt propre de toutes les tâches"""
        self.running = False
        
        logger.info("🛑 ARRÊT PROPRE DES TÂCHES")
        
        await self.taskmaster.stop()
        
    async def get_dashboard_data(self) -> Dict[str, Any]:
        """Données complètes pour dashboard"""
        
        # Données de base
        base_data = await self.integration.get_dashboard_data()
        
        # Ajouter informations sur les paliers
        base_data["thresholds"] = {
            str(amount): info["unlocked"] 
            for amount, info in self.thresholds.items()
        }
        
        # Ajouter uptime
        base_data["orchestrator_uptime"] = (datetime.now() - self.start_time).total_seconds()
        
        # Ajouter statut détaillé des tâches
        task_status = await self.taskmaster.get_all_status()
        base_data["detailed_status"] = task_status
        
        return base_data
        
    async def force_enable_task(self, task_name: str) -> str:
        """Forcer l'activation d'une tâche (pour testing/debug)"""
        try:
            message = await self.taskmaster.enable_task(task_name)
            logger.info(f"🔧 Force activation: {task_name}")
            return message
        except Exception as e:
            logger.error(f"Erreur force activation {task_name}: {e}")
            return f"Erreur: {e}"
            
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Métriques de performance détaillées"""
        
        # Métriques système
        import psutil
        
        system_metrics = {
            "cpu_percent": psutil.cpu_percent(),
            "memory_mb": psutil.Process().memory_info().rss / 1024 / 1024,
            "memory_percent": psutil.Process().memory_percent(),
            "disk_usage": psutil.disk_usage('/').percent
        }
        
        # Métriques des tâches
        task_metrics = await self.taskmaster.get_all_status()
        
        # Calculer performance globale
        total_executions = sum(
            task.get("executions", 0) 
            for task in task_metrics["tasks"].values()
        )
        
        total_errors = sum(
            task.get("errors", 0) 
            for task in task_metrics["tasks"].values()
        )
        
        error_rate = (total_errors / total_executions * 100) if total_executions > 0 else 0
        
        performance_data = {
            "system": system_metrics,
            "tasks": task_metrics,
            "performance": {
                "total_executions": total_executions,
                "total_errors": total_errors,
                "error_rate_percent": error_rate,
                "uptime_hours": (datetime.now() - self.start_time).total_seconds() / 3600,
                "active_tasks": task_metrics["taskmaster"]["active_tasks"],
                "total_tasks": task_metrics["taskmaster"]["total_tasks"]
            }
        }
        
        return performance_data

# Singleton global pour l'orchestrateur
_orchestrator_instance: Optional[MultitaskOrchestrator] = None

def get_orchestrator(database: DatabaseManager) -> MultitaskOrchestrator:
    """Getter pour le singleton orchestrateur"""
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = MultitaskOrchestrator(database)
    return _orchestrator_instance

# Fonctions utilitaires pour usage externe
async def start_multitask_system(database: DatabaseManager):
    """Démarrage complet du système multitâche"""
    orchestrator = get_orchestrator(database)
    
    await orchestrator.initialize()
    await orchestrator.start_all_tasks()
    
    return orchestrator

async def check_balance_and_unlock(database: DatabaseManager, new_balance: float):
    """Vérification du solde et déblocage automatique"""
    orchestrator = get_orchestrator(database)
    
    if orchestrator.running:
        await orchestrator.check_and_unlock_tasks(new_balance)

# Context manager pour usage propre
async def multitask_context(database: DatabaseManager):
    """Context manager pour le système multitâche complet"""
    orchestrator = get_orchestrator(database)
    
    try:
        await orchestrator.initialize()
        await orchestrator.start_all_tasks()
        yield orchestrator
    finally:
        await orchestrator.stop_all_tasks()

# Export pour usage externe
__all__ = [
    'MultitaskOrchestrator',
    'get_orchestrator',
    'start_multitask_system',
    'check_balance_and_unlock',
    'multitask_context'
]
