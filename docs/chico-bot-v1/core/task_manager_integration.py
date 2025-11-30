"""
Integration du TaskMaster avec le bot principal
Points d'entrée pour activation automatique des tâches
"""

import asyncio
from typing import Dict, Any
from .task_manager import get_taskmaster, enable_task_at_threshold
from .database import DatabaseManager

class TaskIntegration:
    """Bridge entre le bot et le TaskMaster"""
    
    def __init__(self, database: DatabaseManager):
        self.database = database
        self.taskmaster = get_taskmaster(database)
        self._last_balance = 0.0
        
    async def register_all_tasks(self):
        """Enregistrement de toutes les tâches avec leurs fonctions"""
        
        # Import des fonctions de tâches ici pour éviter circular imports
        from ..tasks.bounty_tasks import bounty_hunter_main
        from ..tasks.rwa_tasks import rwa_monitor_main  
        from ..tasks.trading_tasks import trading_bot_main
        from ..tasks.investment_tasks import investment_engine_main
        
        # Enregistrement avec configuration automatique
        await self.taskmaster.register_task("bounty_hunter", bounty_hunter_main)
        await self.taskmaster.register_task("rwa_monitor", rwa_monitor_main)
        await self.taskmaster.register_task("trading_bot", trading_bot_main)
        await self.taskmaster.register_task("investment_engine", investment_engine_main)
        
    async def check_balance_thresholds(self, current_balance: float):
        """Vérification des paliers pour activation automatique"""
        
        # Éviter les activations multiples
        if abs(current_balance - self._last_balance) < 0.01:
            return
            
        self._last_balance = current_balance
        
        # Activation selon paliers
        await enable_task_at_threshold("500", current_balance)
        await enable_task_at_threshold("1000", current_balance) 
        await enable_task_at_threshold("2000", current_balance)
        
        # Log spécial pour nouveaux paliers
        if current_balance >= 2000:
            print("🔥 MODE LÉGENDAIRE ACTIVÉ - TOUTES LES TÂCHES ACTIVES 24/7 !")
        elif current_balance >= 1000:
            print("⚡ MODE AVANCÉ ACTIVÉ - 3 TÂCHES SIMULTANÉES !")
        elif current_balance >= 500:
            print("🚀 MODE INTERMÉDIAIRE ACTIVÉ - 2 TÂCHES SIMULTANÉES !")
            
    async def get_dashboard_data(self) -> Dict[str, Any]:
        """Données pour dashboard de monitoring"""
        
        taskmaster_status = await self.taskmaster.get_all_status()
        user_balance = await self.database.get_user_balance()
        
        return {
            "balance": user_balance,
            "active_tasks": taskmaster_status["taskmaster"]["active_tasks"],
            "total_tasks": taskmaster_status["taskmaster"]["total_tasks"],
            "uptime_hours": taskmaster_status["taskmaster"]["uptime"] / 3600,
            "memory_mb": taskmaster_status["taskmaster"]["memory_usage"],
            "cpu_percent": taskmaster_status["taskmaster"]["cpu_usage"],
            "tasks": taskmaster_status["tasks"]
        }

# Singleton pour l'intégration
_integration_instance: TaskIntegration = None

def get_integration(database: DatabaseManager) -> TaskIntegration:
    """Getter singleton pour l'intégration"""
    global _integration_instance
    if _integration_instance is None:
        _integration_instance = TaskIntegration(database)
    return _integration_instance
