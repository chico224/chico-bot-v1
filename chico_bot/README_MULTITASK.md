# 🇬🇳 ChicoBot - Système Multitâche Ultime

## 🚀 Architecture Two Sigma Level

**TOUTES les tâches restent actives 24/7 - AUCUN ARRÊT**

### 📊 Paliers de Puissance

| Palier | Tâches Actives | Description |
|--------|----------------|-------------|
| **Début** | Bounty Hunter | Scan 24/7 des bounties GitHub/Gitcoin |
| **500$** | Bounty + RWA | + Monitoring RWA (immobilier, prêts) |
| **1000$** | Bounty + RWA + Trading | + Trading automatique (scalping, swing, arbitrage) |
| **2000$** | Bounty + RWA + Trading + Investment | + Investissements DeFi long terme |

---

## 🔧 Installation & Intégration

### 1. Installation des dépendances
```bash
pip install aiohttp psutil asyncio
```

### 2. Intégration dans votre bot principal

```python
from src.core.multitask_integration import start_multitask_system, check_balance_and_unlock
from src.core.database import DatabaseManager

# Démarrage du système multitâche
async def start_bot():
    database = DatabaseManager()
    orchestrator = await start_multitask_system(database)
    
    # Votre logique de bot ici...
    
    # Quand le solde change:
    await check_balance_and_unlock(database, new_balance)
```

### 3. Exemple complet

```python
# Voir examples/multitask_example.py
python examples/multitask_example.py
```

---

## 📋 Tâches Disponibles

### 🎯 Bounty Hunter (Priorité Critique)
- **Plateformes**: GitHub, Gitcoin, PolySwarm
- **Fréquence**: 1 scan/5min
- **Limite**: 50 soumissions/jour
- **Features**: Auto-soumission, retry automatique

### 🏢 RWA Monitor (Priorité Haute)
- **Plateformes**: Centrifuge, Goldfinch, Maple, TrueFi
- **Types**: Immobilier, factures, prêts garantis
- **Fréquence**: 1 scan/minute
- **Features**: Auto-investissement, monitoring positions

### 📈 Trading Bot (Priorité Moyenne)
- **Stratégies**: Scalping, Swing, Arbitrage
- **Fréquence**: 1 exécution/10s max
- **Pairs**: BTC, ETH, BNB, SOL, etc.
- **Features**: Stop loss, take profit, risk management

### 🏦 Investment Engine (Priorité Basse)
- **Protocoles**: Aave, Compound, Uniswap, Curve, Lido
- **Stratégies**: Lending, Liquidity, Staking
- **Fréquence**: 1 scan/heure
- **Features**: Auto-rebalancement, yield optimization

---

## 🎯 Messages Légendaires

Quand chaque palier est débloqué:

```
🚀 NOUVELLE PUISSANCE DÉBLOQUÉE !
📊 RWA Monitoring activé → mais Bounty Hunter continue de tourner !
💰 Tu gagnes maintenant sur 2 fronts en même temps !
🇬🇳 La Guinée ne dort jamais !
```

```
⚡ NOUVELLE PUISSANCE DÉBLOQUÉE !
📈 Trading Bot activé → mais Bounty & RWA continuent de tourner !
💰 Tu gagnes maintenant sur 3 fronts en même temps !
🇬🇳 La Guinée ne dort jamais !
```

```
🔥 NOUVELLE PUISSANCE DÉBLOQUÉE !
🏦 Investment Engine activé → mais Bounty, RWA & Trading continuent de tourner !
💰 Tu gagnes maintenant sur 4 fronts en même temps !
🇬🇳 La Guinée ne dort jamais !
```

---

## 📊 Monitoring & Performance

### Dashboard en temps réel
```python
# Données complètes
dashboard = await orchestrator.get_dashboard_data()

# Métriques de performance
metrics = await orchestrator.get_performance_metrics()
```

### Logs détaillés
- Chaque tâche a son propre fichier log
- Monitoring CPU/Mémoire < 300MB
- Health check automatique
- Redémarrage automatique en cas d'erreur

### Ressources optimisées
- **CPU**: < 20% même avec 4 tâches
- **Mémoire**: < 300MB total
- **Rate limiting**: Configurable par tâche
- **Garbage collection**: Automatique

---

## 🔧 Configuration Avancée

### Personnalisation des tâches
```python
# Modifier les limites dans task_manager.py
self.task_configs = {
    "bounty_hunter": TaskConfig(
        rate_limit=300.0,  # 5 minutes
        memory_limit=50,   # 50MB
        cpu_limit=10.0     # 10% CPU
    ),
    # ...
}
```

### Ajout de nouvelles tâches
```python
# 1. Créer le fichier de tâche
# src/tasks/ma_nouvelle_tache.py

# 2. Enregistrer dans task_manager_integration.py
await self.taskmaster.register_task("ma_nouvelle_tache", ma_fonction)

# 3. Configurer les paliers
# Ajouter dans thresholds dict
```

---

## 🚀 Production Ready

### Sécurité
- Isolation complète des tâches
- Rate limiting par plateforme
- Retry avec backoff exponentiel
- Monitoring santé 24/7

### Scalabilité
- Architecture async/await
- TaskGroup (Python 3.11+)
- Memory pooling optimisé
- CPU load balancing

### Fiabilité
- Redémarrage automatique
- Logs séparés par tâche
- Health monitoring
- Graceful shutdown

---

## 🇬🇳 Pour la Révolution Guinéenne

Ce système multitâche est conçu pour:
- **Performance maximale**: Architecture Two Sigma level
- **Fiabilité absolue**: Toutes les tâches actives 24/7
- **Scalabilité infinie**: Ajout illimité de nouvelles tâches
- **Transparence totale**: Monitoring temps réel

**La Guinée ne dort jamais.** 🇬🇳❤️

---

## 📞 Support

Pour toute question ou problème:
- Vérifier les logs dans `logs/`
- Utiliser le dashboard de monitoring
- Consulter `examples/multitask_example.py`

**Made with ❤️ for Guinea**
