"""
Exemple d'utilisation du système multitâche
Montre comment intégrer le TaskMaster dans votre bot principal
"""

import asyncio
import logging
from datetime import datetime

# Import des modules multitâche
from src.core.multitask_integration import start_multitask_system, check_balance_and_unlock
from src.core.database import DatabaseManager
from src.core.logging_setup import setup_logging

logger = setup_logging("multitask_example")

class ChicoBotWithMultitask:
    """
    Bot Chico avec système multitâche intégré
    Architecture Two Sigma level - Performance maximale
    """
    
    def __init__(self):
        self.database = DatabaseManager()
        self.orchestrator = None
        self.running = False
        
    async def initialize(self):
        """Initialisation du bot avec multitâche"""
        logger.info("🇬🇳 Initialisation ChicoBot Multitâche...")
        
        # Démarrer le système multitâche
        self.orchestrator = await start_multitask_system(self.database)
        
        logger.info("✅ ChicoBot Multitâche prêt")
        
    async def start(self):
        """Démarrage principal du bot"""
        self.running = True
        
        logger.info("🚀 CHICOBOT MULTITÂCHE DÉMARRÉ")
        logger.info("📊 Toutes les tâches actives 24/7 en parallèle")
        logger.info("🎯 Paliers: 500$ → 1000$ → 2000$")
        
        # Boucle principale du bot
        while self.running:
            try:
                # Simulation de nouvelles transactions/dépôts
                await self.simulate_transactions()
                
                # Afficher dashboard périodiquement
                if datetime.now().second % 30 == 0:
                    await self.show_dashboard()
                
                await asyncio.sleep(1)  # Check chaque seconde
                
            except KeyboardInterrupt:
                logger.info("🛑 Arrêt demandé par l'utilisateur")
                break
            except Exception as e:
                logger.error(f"Erreur boucle principale: {e}")
                await asyncio.sleep(5)
                
    async def simulate_transactions(self):
        """Simulation de transactions pour démonstration"""
        
        # Simuler un dépôt toutes les 10 secondes
        if datetime.now().second % 10 == 0:
            import random
            
            # Dépôt aléatoire entre 50$ et 500$
            deposit_amount = random.uniform(50, 500)
            
            # Mettre à jour le solde
            current_balance = await self.database.get_user_balance()
            new_balance = current_balance + deposit_amount
            
            await self.database.update_user_balance(new_balance)
            
            logger.info(f"💰 Nouveau dépôt: +{deposit_amount:.2f}$ → Solde: {new_balance:.2f}$")
            
            # Vérifier si on débloque de nouvelles tâches
            await check_balance_and_unlock(self.database, new_balance)
            
    async def show_dashboard(self):
        """Afficher le dashboard de performance"""
        
        if not self.orchestrator:
            return
            
        try:
            # Données du dashboard
            dashboard_data = await self.orchestrator.get_dashboard_data()
            performance_data = await self.orchestrator.get_performance_metrics()
            
            # Affichage console
            print("\n" + "="*60)
            print(f"🇬🇳 CHICOBOT DASHBOARD - {datetime.now().strftime('%H:%M:%S')}")
            print("="*60)
            
            # Solde et paliers
            print(f"💰 Solde: {dashboard_data['balance']:.2f}$")
            print(f"🎯 Paliers débloqués:")
            for threshold, unlocked in dashboard_data['thresholds'].items():
                status = "✅" if unlocked else "🔒"
                print(f"   ${threshold}: {status}")
                
            # Tâches actives
            print(f"\n📊 Tâches actives: {dashboard_data['active_tasks']}/{dashboard_data['total_tasks']}")
            
            # Performance système
            perf = performance_data['performance']
            print(f"\n⚡ Performance:")
            print(f"   Exécutions totales: {perf['total_executions']}")
            print(f"   Erreurs: {perf['total_errors']}")
            print(f"   Taux d'erreur: {perf['error_rate_percent']:.2f}%")
            print(f"   Uptime: {perf['uptime_hours']:.1f}h")
            
            # Ressources système
            system = performance_data['system']
            print(f"\n🧠 Ressources:")
            print(f"   CPU: {system['cpu_percent']:.1f}%")
            print(f"   Mémoire: {system['memory_mb']:.1f}MB ({system['memory_percent']:.1f}%)")
            print(f"   Disque: {system['disk_usage']:.1f}%")
            
            # Détail des tâches
            print(f"\n📋 Détail tâches:")
            tasks = performance_data['tasks']['tasks']
            for task_name, task_data in tasks.items():
                if task_data['enabled']:
                    status_emoji = "🟢"
                else:
                    status_emoji = "🔒"
                    
                print(f"   {status_emoji} {task_name}:")
                print(f"      ✅ Exécutions: {task_data['executions']}")
                print(f"      ❌ Erreurs: {task_data['errors']}")
                print(f"      ⏱️  Temps moyen: {task_data['avg_execution_time']:.2f}s")
                    
            print("="*60)
            
        except Exception as e:
            logger.error(f"Erreur dashboard: {e}")
            
    async def stop(self):
        """Arrêt propre du bot"""
        self.running = False
        
        logger.info("🛑 Arrêt de ChicoBot Multitâche...")
        
        if self.orchestrator:
            await self.orchestrator.stop_all_tasks()

# Point d'entrée principal
async def main():
    """Point d'entrée pour démonstration"""
    
    print("🇬🇳 CHICOBOT MULTITÂCHE - DÉMONSTRATION")
    print("="*60)
    print("📊 Architecture multitâche 24/7")
    print("🎯 Paliers: 500$ → RWA, 1000$ → Trading, 2000$ → Investment")
    print("🔥 Toutes les tâches restent actives en parallèle")
    print("🇬🇳 La Guinée ne dort jamais !")
    print("="*60)
    
    # Créer et démarrer le bot
    bot = ChicoBotWithMultitask()
    
    try:
        await bot.initialize()
        await bot.start()
    except KeyboardInterrupt:
        print("\n🛑 Interruption utilisateur")
    finally:
        await bot.stop()
        print("🇬🇳 ChicoBot Multitâche arrêté. À bientôt !")

# Démarrer la démonstration
if __name__ == "__main__":
    asyncio.run(main())
