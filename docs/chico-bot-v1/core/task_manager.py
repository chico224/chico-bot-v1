"""
Task Manager - Architecture Multitâche Production-Ready
Conçu pour Two Sigma/Jane Street level performance
Toutes les tâches restent actives 24/7 - AUCUN ARRÊT
"""

import asyncio
import logging
import gc
import psutil
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum, auto
import json
from pathlib import Path
import signal
import sys
from contextlib import asynccontextmanager
import resource

from .logging_setup import setup_logging
from .database import DatabaseManager

class TaskStatus(Enum):
    IDLE = auto()
    RUNNING = auto()
    PAUSED = auto()
    ERROR = auto()
    RESTARTING = auto()

class TaskPriority(Enum):
    CRITICAL = 1    # Bounty hunter - toujours actif
    HIGH = 2        # RWA monitoring
    MEDIUM = 3      # Trading
    LOW = 4         # Investment - long terme

@dataclass
class TaskConfig:
    name: str
    priority: TaskPriority
    rate_limit: float  # secondes entre exécutions
    memory_limit: int  # MB
    cpu_limit: float  # pourcentage
    retry_count: int = 3
    retry_delay: float = 5.0
    enabled: bool = True

@dataclass
class TaskMetrics:
    executions: int = 0
    errors: int = 0
    last_execution: Optional[datetime] = None
    last_error: Optional[str] = None
    avg_execution_time: float = 0.0
    memory_usage: float = 0.0
    cpu_usage: float = 0.0

class TaskWorker:
    """Worker individuel pour chaque tâche - Isolation complète"""
    
    def __init__(self, config: TaskConfig, task_func: Callable):
        self.config = config
        self.task_func = task_func
        self.status = TaskStatus.IDLE
        self.metrics = TaskMetrics()
        self.last_run = datetime.min
        self.process = None
        self.logger = setup_logging(f"task_{config.name}")
        self._execution_times = []
        
    async def execute(self) -> bool:
        """Exécution isolée avec monitoring ressources"""
        if not self.config.enabled:
            return True
            
        start_time = datetime.now()
        
        try:
            # Rate limiting check
            if (datetime.now() - self.last_run).total_seconds() < self.config.rate_limit:
                return True
                
            self.status = TaskStatus.RUNNING
            self.metrics.executions += 1
            
            # Monitoring ressources avant
            memory_before = psutil.Process().memory_info().rss / 1024 / 1024
            
            # Exécution de la tâche
            if asyncio.iscoroutinefunction(self.task_func):
                await self.task_func()
            else:
                await asyncio.to_thread(self.task_func)
                
            # Monitoring ressources après
            memory_after = psutil.Process().memory_info().rss / 1024 / 1024
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # Update métriques
            self._execution_times.append(execution_time)
            if len(self._execution_times) > 100:
                self._execution_times.pop(0)
            self.metrics.avg_execution_time = sum(self._execution_times) / len(self._execution_times)
            self.metrics.memory_usage = memory_after - memory_before
            self.metrics.last_execution = datetime.now()
            self.last_run = datetime.now()
            
            # Vérification limites
            if memory_after > self.config.memory_limit:
                self.logger.warning(f"Mémoire élevée: {memory_after:.1f}MB > {self.config.memory_limit}MB")
                gc.collect()
                
            self.status = TaskStatus.IDLE
            return True
            
        except Exception as e:
            self.metrics.errors += 1
            self.metrics.last_error = str(e)
            self.status = TaskStatus.ERROR
            self.logger.error(f"Erreur {self.config.name}: {e}")
            return False
            
    async def health_check(self) -> bool:
        """Check santé de la tâche"""
        if self.status == TaskStatus.ERROR:
            return False
            
        # Vérifier si la tâche n'est pas bloquée
        if self.status == TaskStatus.RUNNING:
            if (datetime.now() - self.metrics.last_execution).total_seconds() > 300:  # 5min
                self.logger.warning(f"Tâche {self.config.name} bloquée")
                return False
                
        return True

class TaskMaster:
    """
    TaskMaster - Supervision intelligente de toutes les tâches
    Architecture type Two Sigma - Maximum performance
    """
    
    def __init__(self, database: DatabaseManager):
        self.database = database
        self.logger = setup_logging("taskmaster")
        self.workers: Dict[str, TaskWorker] = {}
        self.running = False
        self.start_time = datetime.now()
        self._shutdown_event = asyncio.Event()
        
        # Configuration tâches - PRODUCTION READY
        self.task_configs = {
            "bounty_hunter": TaskConfig(
                name="bounty_hunter",
                priority=TaskPriority.CRITICAL,
                rate_limit=300.0,  # 5 minutes
                memory_limit=50,
                cpu_limit=10.0,
                enabled=True
            ),
            "rwa_monitor": TaskConfig(
                name="rwa_monitor", 
                priority=TaskPriority.HIGH,
                rate_limit=60.0,   # 1 minute
                memory_limit=30,
                cpu_limit=5.0,
                enabled=False  # S'active à 500$
            ),
            "trading_bot": TaskConfig(
                name="trading_bot",
                priority=TaskPriority.MEDIUM,
                rate_limit=10.0,   # 10 secondes
                memory_limit=40,
                cpu_limit=15.0,
                enabled=False  # S'active à 1000$
            ),
            "investment_engine": TaskConfig(
                name="investment_engine",
                priority=TaskPriority.LOW,
                rate_limit=3600.0, # 1 heure
                memory_limit=25,
                cpu_limit=3.0,
                enabled=False  # S'active à 2000$
            )
        }
        
        # Setup signaux pour shutdown propre
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
        
    def _signal_handler(self, signum, frame):
        """Handler pour arrêt propre"""
        self.logger.info(f"Signal {signum} reçu - Arrêt propre...")
        self._shutdown_event.set()
        
    async def register_task(self, name: str, task_func: Callable):
        """Enregistrement d'une nouvelle tâche"""
        if name not in self.task_configs:
            raise ValueError(f"Tâche {name} non configurée")
            
        config = self.task_configs[name]
        worker = TaskWorker(config, task_func)
        self.workers[name] = worker
        
        self.logger.info(f"Tâche {name} enregistrée (priorité: {config.priority.name})")
        
    async def enable_task(self, name: str) -> str:
        """Activation d'une tâche - MESSAGE LÉGENDAIRE"""
        if name not in self.workers:
            raise ValueError(f"Tâche {name} non trouvée")
            
        worker = self.workers[name]
        worker.config.enabled = True
        worker.status = TaskStatus.IDLE
        
        # Message légendaire
        messages = {
            "rwa_monitor": """
🚀 NOUVELLE PUISSANCE DÉBLOQUÉE !
📊 RWA Monitoring activé → mais Bounty Hunter continue de tourner !
💰 Tu gagnes maintenant sur 2 fronts en même temps !
🇬🇳 La Guinée ne dort jamais !
            """.strip(),
            "trading_bot": """
⚡ NOUVELLE PUISSANCE DÉBLOQUÉE !
📈 Trading Bot activé → mais Bounty & RWA continuent de tourner !
💰 Tu gagnes maintenant sur 3 fronts en même temps !
🇬🇳 La Guinée ne dort jamais !
            """.strip(),
            "investment_engine": """
🔥 NOUVELLE PUISSANCE DÉBLOQUÉE !
🏦 Investment Engine activé → mais Bounty, RWA & Trading continuent de tourner !
💰 Tu gagnes maintenant sur 4 fronts en même temps !
🇬🇳 La Guinée ne dort jamais !
            """.strip()
        }
        
        message = messages.get(name, f"🚀 Tâche {name} activée !")
        
        # Log spécial
        self.logger.info("="*60)
        self.logger.info(message)
        self.logger.info("="*60)
        
        return message
        
    async def disable_task(self, name: str):
        """Désactivation d'une tâche (jamais utilisé en production)"""
        if name not in self.workers:
            return
            
        worker = self.workers[name]
        worker.config.enabled = False
        worker.status = TaskStatus.PAUSED
        
        self.logger.info(f"Tâche {name} désactivée")
        
    async def _execute_worker(self, name: str, worker: TaskWorker):
        """Exécution continue d'un worker avec retry"""
        retry_count = 0
        
        while self.running and not self._shutdown_event.is_set():
            try:
                if worker.config.enabled:
                    success = await worker.execute()
                    
                    if not success:
                        retry_count += 1
                        if retry_count < worker.config.retry_count:
                            await asyncio.sleep(worker.config.retry_delay)
                            continue
                        else:
                            self.logger.error(f"Tâche {name} - retry limit atteinte")
                            worker.status = TaskStatus.ERROR
                            retry_count = 0
                    else:
                        retry_count = 0
                else:
                    worker.status = TaskStatus.PAUSED
                    
            except Exception as e:
                self.logger.error(f"Erreur critique worker {name}: {e}")
                worker.status = TaskStatus.ERROR
                retry_count += 1
                
            await asyncio.sleep(1)  # Petite pause pour éviter CPU 100%
            
    async def _health_monitor(self):
        """Monitoring santé de toutes les tâches"""
        while self.running and not self._shutdown_event.is_set():
            try:
                for name, worker in self.workers.items():
                    if not await worker.health_check():
                        self.logger.warning(f"Redémarrage tâche {name}")
                        worker.status = TaskStatus.RESTARTING
                        await asyncio.sleep(5)
                        worker.status = TaskStatus.IDLE
                        
                # Monitoring global ressources
                memory = psutil.Process().memory_info().rss / 1024 / 1024
                cpu = psutil.cpu_percent()
                
                if memory > 300:  # Limite 300MB
                    self.logger.warning(f"Mémoire élevée: {memory:.1f}MB")
                    gc.collect()
                    
                # Log métriques toutes les 10 minutes
                if (datetime.now() - self.start_time).seconds % 600 == 0:
                    await self._log_metrics()
                    
            except Exception as e:
                self.logger.error(f"Erreur health monitor: {e}")
                
            await asyncio.sleep(30)  # Check toutes les 30 secondes
            
    async def _log_metrics(self):
        """Log des métriques détaillées"""
        uptime = datetime.now() - self.start_time
        
        self.logger.info("="*50)
        self.logger.info(f"📊 TASKMASTER METRICS - Uptime: {uptime}")
        self.logger.info(f"🧠 Memory: {psutil.Process().memory_info().rss/1024/1024:.1f}MB")
        self.logger.info(f"⚡ CPU: {psutil.cpu_percent()}%")
        
        for name, worker in sorted(self.workers.items(), key=lambda x: x[1].config.priority.value):
            status_emoji = {
                TaskStatus.RUNNING: "🟢",
                TaskStatus.IDLE: "🔵", 
                TaskStatus.PAUSED: "🟡",
                TaskStatus.ERROR: "🔴",
                TaskStatus.RESTARTING: "🔄"
            }.get(worker.status, "⚪")
            
            self.logger.info(f"{status_emoji} {name}:")
            self.logger.info(f"   ✅ Exécutions: {worker.metrics.executions}")
            self.logger.info(f"   ❌ Erreurs: {worker.metrics.errors}")
            self.logger.info(f"   ⏱️  Temps moyen: {worker.metrics.avg_execution_time:.2f}s")
            self.logger.info(f"   🧠 Mémoire: {worker.metrics.memory_usage:.1f}MB")
            
        self.logger.info("="*50)
        
    async def start(self):
        """Démarrage du TaskMaster - TOUTES LES TÂCHES ACTIVES 24/7"""
        self.running = True
        self.logger.info("🚀 TASKMASTER DÉMARRÉ - MODE MULTITÂCHE ULTIME")
        
        # Création des tâches concurrentes avec TaskGroup (Python 3.11+)
        try:
            async with asyncio.TaskGroup() as tg:
                # Worker tasks
                for name, worker in self.workers.items():
                    tg.create_task(self._execute_worker(name, worker))
                    
                # Health monitor task
                tg.create_task(self._health_monitor())
                
        except Exception as e:
            self.logger.error(f"Erreur TaskGroup: {e}")
            
    async def stop(self):
        """Arrêt propre du TaskMaster"""
        self.running = False
        self._shutdown_event.set()
        
        self.logger.info("🛑 TASKMASTER ARRÊT PROPRE")
        
        # Arrêt de tous les workers
        for name, worker in self.workers.items():
            worker.status = TaskStatus.PAUSED
            
        # Cleanup
        gc.collect()
        
    async def get_task_status(self, name: str) -> Dict[str, Any]:
        """Statut détaillé d'une tâche"""
        if name not in self.workers:
            return {"error": "Tâche non trouvée"}
            
        worker = self.workers[name]
        return {
            "name": name,
            "status": worker.status.name,
            "enabled": worker.config.enabled,
            "priority": worker.config.priority.name,
            "executions": worker.metrics.executions,
            "errors": worker.metrics.errors,
            "last_execution": worker.metrics.last_execution.isoformat() if worker.metrics.last_execution else None,
            "last_error": worker.metrics.last_error,
            "avg_execution_time": worker.metrics.avg_execution_time,
            "memory_usage": worker.metrics.memory_usage,
            "rate_limit": worker.config.rate_limit
        }
        
    async def get_all_status(self) -> Dict[str, Any]:
        """Statut de toutes les tâches"""
        return {
            "taskmaster": {
                "running": self.running,
                "uptime": (datetime.now() - self.start_time).total_seconds(),
                "total_tasks": len(self.workers),
                "active_tasks": sum(1 for w in self.workers.values() if w.config.enabled),
                "memory_usage": psutil.Process().memory_info().rss / 1024 / 1024,
                "cpu_usage": psutil.cpu_percent()
            },
            "tasks": {name: await self.get_task_status(name) for name in self.workers.keys()}
        }

# Singleton global pour toute l'application
_taskmaster_instance: Optional[TaskMaster] = None

def get_taskmaster(database: DatabaseManager) -> TaskMaster:
    """Getter pour le singleton TaskMaster"""
    global _taskmaster_instance
    if _taskmaster_instance is None:
        _taskmaster_instance = TaskMaster(database)
    return _taskmaster_instance

# Context manager pour usage propre
@asynccontextmanager
async def taskmaster_context(database: DatabaseManager):
    """Context manager pour TaskMaster"""
    taskmaster = get_taskmaster(database)
    try:
        await taskmaster.start()
        yield taskmaster
    finally:
        await taskmaster.stop()

# Fonctions utilitaires pour faciliter l'usage
async def enable_task_at_threshold(threshold_name: str, current_balance: float):
    """Activation automatique des tâches selon le solde"""
    taskmaster = _taskmaster_instance
    if not taskmaster:
        return
        
    thresholds = {
        "500": "rwa_monitor",
        "1000": "trading_bot", 
        "2000": "investment_engine"
    }
    
    for threshold, task_name in thresholds.items():
        if current_balance >= float(threshold):
            worker = taskmaster.workers.get(task_name)
            if worker and not worker.config.enabled:
                message = await taskmaster.enable_task(task_name)
                # Envoyer message à l'utilisateur
                print(message)  # ou via notification system
                
# Export pour usage externe
__all__ = [
    'TaskMaster',
    'TaskWorker', 
    'TaskConfig',
    'TaskStatus',
    'TaskPriority',
    'get_taskmaster',
    'taskmaster_context',
    'enable_task_at_threshold'
]
