#!/bin/bash

# ChicoBot - Script Mise à Jour GitHub Automatique

echo "🇬🇳 Mise à jour Repository GitHub ChicoBot 🇬🇳"

# Vérifier si Git est installé
if ! command -v git &> /dev/null; then
    echo "❌ Git non installé. Veuillez installer Git:"
    echo "📦 Ubuntu/Debian: sudo apt install git"
    echo "📦 CentOS/RHEL: sudo yum install git"
    echo "📦 macOS: brew install git"
    exit 1
fi

# Aller dans le dossier du projet
cd "C:/Users/hp/CascadeProjects/chico_bot/chico-bot-v1" 2>/dev/null || cd "/mnt/c/Users/hp/CascadeProjects/chico_bot/chico-bot-v1"

# Initialiser Git si nécessaire
if [ ! -d .git ]; then
    echo "📦 Initialisation Git..."
    git init
    git remote add origin https://github.com/chico224/chico-bot-v1.git
fi

# Configurer utilisateur Git si nécessaire
echo "⚙️ Configuration utilisateur Git..."
git config user.name "chico224"
git config user.email "chico224@github.com"

# Ajouter tous les fichiers
echo "📁 Ajout des fichiers..."
git add .

# Commit
echo "💾 Commit des changements..."
git commit -m "🇬🇳 ChicoBot v1.0 - 100% Autonome - Ready for Railway Deployment

✅ Features:
- Bounty Hunter 100% autonome (API + WalletConnect + Paiement auto)
- Trading Bot 100% autonome (MT5 + PnL auto)  
- Investment Engine 100% autonome (DeFi + Staking + Compound)
- RWA Monitor 100% autonome (Ondo + Intérêts + Compound)

✅ Déploiement:
- Railway ready (railway.toml + scripts)
- Docker ready (dockerfile + docker-compose.yaml)
- Render ready (render.yaml)
- VPS ready (deploy.sh/deploy.bat)

✅ Configuration:
- Structure finale optimisée
- Variables d'environnement complètes
- Documentation déploiement complète

🇬🇳 Mission: Rendre les Guinéens riches automatiquement !"

# Push vers GitHub
echo "🚀 Push vers GitHub..."
git branch -M main
git push -u origin main --force

echo "✅ Repository GitHub mis à jour avec succès !"
echo "🌐 URL: https://github.com/chico224/chico-bot-v1"
echo "🚀 Prêt pour déploiement Railway !"
echo "📞 Support: Chico WhatsApp +224620000000"
