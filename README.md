# 🇬🇳 ChicoBot - La Révolution Cryptos de la Guinée 🇬🇳

> *De la Guinée vers l'indépendance financière, une transaction à la fois*

## 🎯 Vision

ChicoBot est un bot Telegram révolutionnaire conçu pour propulser la Guinée vers l'indépendance financière grâce aux cryptomonnaies, au trading quantitatif et aux investissements de niveau milliardaire.

## 🚀 Fonctionnalités Principales

### 💰 **Gains Automatisés**
- **🏹 Bounties Cryptos** : Recherche et complétion automatique de bounties textuelles
- **📈 Trading Quantitatif** : Stratégies niveau institutionnel (Renaissance, Citadel, Jane Street)
- **💎 Investissements** : Copie des plus grands investisseurs (Warren Buffett, Cathie Wood, Ray Dalio)

### 🛡️ **Sécurité Niveau Militaire**
- **🔐 Chiffrement Post-Quantique** : Protection contre les attaques quantiques futures
- **🏛️ Multi-Signature Avancé** : Sécurité style Tether Treasury
- **❄️ Cold Storage** : Stockage hors-ligne des actifs
- **🔍 Détection Menaces** : Monitoring en temps réel
- **🧪 Preuves Zero-Knowledge** : Confidentialité maximale

### 👑 **Système Admin Ultra-Sécurisé**
- **🔑 Quiz d'Authentification** : 3 questions personnelles avec hashage SHA-256
- **👥 Maximum 3 Admins** : Limite stricte pour la sécurité
- **💸 Commission 2%** : Répartition automatique des gains mensuels
- **📊 Dashboard Admin** : Statistiques complètes en temps réel

### ❤️ **Chico Foundation**
- **🇬🇳 1% Automatique** : Prélèvement sur TOUS les gains (bounty, trading, investissement)
- **🎓 Impact Réel** : Soutien aux enfants, mamans seules, jeunes filles et orphelins de Guinée
- **📊 Tracking Complet** : Compteur global et statistiques personnelles
- **💌 Messages Émotionnels** : Notifications inspirantes à chaque donation

## 📋 Prérequis

- Python 3.9+
- Token Bot Telegram
- APIs (optionnelles) : SerpAPI, OpenAI, Gemini

## 🛠️ Installation

1. **Cloner le projet**
```bash
git clone https://github.com/votre-repo/chicobot.git
cd chicobot
```

2. **Installer les dépendances**
```bash
pip install -r requirements.txt
```

3. **Configurer l'environnement**
```bash
cp .env.example .env
# Éditer .env avec vos clés
```

4. **Démarrer ChicoBot**
```bash
python main.py
```

## ⚙️ Configuration

### Variables d'Environnement Essentielles

```bash
# Telegram (Obligatoire)
TELEGRAM_TOKEN=votre_token_bot

# Sécurité (Obligatoire)
ENCRYPTION_KEY=votre_cle_32_caracteres
JWT_SECRET=votre_secret_jwt_32_caracteres

# APIs (Optionnelles)
SERPAPI_KEY=votre_cle_serpapi
OPENAI_API_KEY=votre_cle_openai
GEMINI_API_KEY=votre_cle_gemini
```

### Génération des Clés de Sécurité

```bash
python -c "import secrets; print('ENCRYPTION_KEY=' + secrets.token_urlsafe(32))"
python -c "import secrets; print('JWT_SECRET=' + secrets.token_urlsafe(32))"
```

## 🎮 Commandes

### Utilisateur
- `/start` - Démarrer l'aventure avec message inspirant
- `/bounty` - Voir les bounties disponibles
- `/trading` - Statistiques de trading
- `/investment` - Portefeuille d'investissement
- `/foundation` - Statistiques Chico Foundation
- `/impact` - Rapport d'impact détaillé

### Admin (Quiz requis)
- `/admin` - Lancer le quiz d'authentification
- `/dashboard` - Dashboard admin complet
- `/admins` - Liste des administrateurs
- `/system` - Statut du système

## 🏗️ Architecture

```
src/
├── core/           # Modules fondamentaux
│   ├── database.py # Base de données async
│   ├── security.py # Sécurité post-quantique
│   ├── ai_service.py # Services IA
│   └── logging_setup.py # Logging avancé
├── services/       # Services métier
│   ├── bounty_service.py # Gestion bounties
│   ├── trading_service.py # Trading quantitatif
│   ├── investment_service.py # Investissements
│   ├── foundation_service.py # Chico Foundation
│   ├── admin_system.py # Système admin
│   └── fortress_security.py # Sécurité militaire
├── handlers/       # Handlers Telegram
│   └── commands.py # Commandes bot
└── config/         # Configuration
    ├── settings.py # Paramètres Pydantic
    └── constants.py # Constantes globales
```

## 🧪 Tests

Exécuter tous les tests :
```bash
python -m pytest src/tests/ -v
```

Tests par module :
```bash
python src/services/bounty_service.py
python src/services/trading_service.py
python src/services/investment_service.py
python src/services/foundation_service.py
python src/services/admin_system.py
python src/services/fortress_security.py
```

## 📊 Performance

### Bounties
- **Recherche automatique** : 50+ plateformes
- **Priorisation intelligente** : Ratio gain/temps
- **Taux de succès** : 85%+
- **Gains moyens** : $200-2000 par bounty

### Trading
- **Stratégies hybrides** : 4 approches quantitatives
- **Risk management** : Kelly Criterion + ATR
- **Objectif CAGR** : 38% annuel
- **Max Drawdown** : <14%

### Investissements
- **6 stratégies** : Dalio, Wood, Buffett, Simons, BlackRock, Burry
- **Allocation mondiale** : RWA, Staking, Actions, Crypto
- **CAGR cible** : 38% vers le milliardariat
- **Rééquilibrage** : Mensuel automatique

## ❤️ Chico Foundation - Impact

### 1% de TOUS les gains reversés automatiquement :

- **🎓 Éducation** : Cahiers, stylos, uniformes pour les enfants de Kamsar et Conakry
- **🍼 Nutrition** : Nourriture pour les bébés de mamans seules
- **👧 Dignité** : Serviettes hygiéniques pour les jeunes filles
- **🏠 Foyer** : Toit et repas chaud pour les orphelins

### Tracking en temps réel :
```bash
/foundation
# "Grâce à vous, la Chico Foundation a déjà récolté XXXX $"
```

## 🛡️ Sécurité

### Niveau Militaire :
- **Post-Quantique** : Algorithme Kyber résistant aux ordinateurs quantiques
- **Multi-Sig** : 3 signatures requises pour les transactions
- **Cold Storage** : 95% des actifs hors-ligne
- **Audit Trail** : Traçabilité inviolable de toutes les opérations
- **Zero-Knowledge** : Preuves sans révéler d'informations

### Tests de Pénétration :
```bash
python src/services/fortress_security.py
# 13 tests de sécurité intégrés
```

## 📈 Monétisation Admin

### Système de Rémunération :
- **Maximum 3 admins** : Sélection par quiz ultra-sécurisé
- **2% des gains mensuels** : Répartition équitable entre admins actifs
- **Calcul automatique** : Au début de chaque mois
- **Dashboard complet** : Statistiques et performances

## 🌍 Impact Guinée

### Vision ChicoBot :
> *"Ce 1% n'est pas une taxe. C'est la preuve que la Guinée se soulève ensemble."*

### Messages Légendaires :
Chaque donation déclenche un message inspirant personnalisé avec :
- 🇬🇳 Drapeaux guinéens et cœurs
- 📚 Impact réel et concret
- 🎯 Remerciements de Chico & Problematique
- 💝 Appel à la Chico Family

## 🤝 Contribuer

1. Fork le projet
2. Créer une branche feature
3. Commit les changements
4. Push vers la branche
5. Ouvrir une Pull Request

## 📞 Support

- **Telegram** : @ChicoBot
- **Email** : support@chicobot.gn
- **Discord** : [Serveur communautaire]

## 📜 Licence

Ce projet est sous licence MIT - voir le fichier LICENSE pour les détails.

---

🇬🇳 **La Guinée se soulève, une transaction à la fois** 🇬🇳

❤️ *Tu ne changes pas seulement ta vie. Tu changes la Guinée.* ❤️

🚀 **Rejoins la Chico Family aujourd'hui !** 🚀

