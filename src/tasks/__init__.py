"""
Package des tâches pour le TaskMaster
Chaque tâche est isolée et optimisée pour exécution 24/7
"""

# Imports des tâches principales
from .bounty_tasks import bounty_hunter_main
from .rwa_tasks import rwa_monitor_main  
from .trading_tasks import trading_bot_main
from .investment_tasks import investment_engine_main

__all__ = [
    'bounty_hunter_main',
    'rwa_monitor_main', 
    'trading_bot_main',
    'investment_engine_main'
]
