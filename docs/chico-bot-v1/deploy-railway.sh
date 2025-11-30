# ChicoBot - Script Déploiement Railway Automatique

#!/bin/bash

echo "🇬🇳 Déploiement automatique ChicoBot sur Railway 🇬🇳"

# Vérification prérequis
if ! command -v npm &> /dev/null; then
    echo "❌ Node.js/npm non installé"
    echo "📦 Installation Node.js : https://nodejs.org/"
    exit 1
fi

# Installation CLI Railway
echo "📦 Installation Railway CLI..."
npm install -g @railway/cli

# Login Railway
echo "🔑 Login Railway..."
railway login

# Initialisation projet
echo "🚀 Initialisation projet Railway..."
railway init

# Variables d'environnement obligatoires
echo "⚙️ Configuration variables..."

# Bot Telegram
echo "🤖 Configuration Bot Telegram..."
read -p "TELEGRAM_BOT_TOKEN: " telegram_token
railway variables set TELEGRAM_BOT_TOKEN=$telegram_token

read -p "TELEGRAM_ADMIN_CHAT_ID: " admin_chat_id
railway variables set TELEGRAM_ADMIN_CHAT_ID=$admin_chat_id

# Wallet Utilisateur
echo "💰 Configuration Wallet..."
read -p "WALLET_PRIVATE_KEY: " wallet_key
railway variables set WALLET_PRIVATE_KEY=$wallet_key

# Trading MT5
echo "📊 Configuration Trading MT5..."
read -p "MT5_LOGIN: " mt5_login
railway variables set MT5_LOGIN=$mt5_login

read -p "MT5_PASSWORD: " mt5_password
railway variables set MT5_PASSWORD=$mt5_password

read -p "MT5_SERVER: " mt5_server
railway variables set MT5_SERVER=$mt5_server

# Foundation
echo "🏛️ Configuration Foundation..."
read -p "FOUNDATION_WALLET: " foundation_wallet
railway variables set FOUNDATION_WALLET=$foundation_wallet

# APIs IA
echo "🧠 Configuration APIs IA..."
read -p "OPENAI_PROJECT_API_KEY: " openai_key
railway variables set OPENAI_PROJECT_API_KEY=$openai_key

read -p "GEMINI_API_KEY: " gemini_key
railway variables set GEMINI_API_KEY=$gemini_key

# Sécurité
echo "🔐 Configuration Sécurité..."
read -p "ENCRYPTION_KEY (32 chars min): " encryption_key
railway variables set ENCRYPTION_KEY=$encryption_key

read -p "JWT_SECRET (32 chars min): " jwt_secret
railway variables set JWT_SECRET=$jwt_secret

# Support Chico
echo "📞 Configuration Support..."
railway variables set CHICO_WHATSAPP="+224620000000"
railway variables set CHICO_CALL="+224620000001"
railway variables set PROBLEMATIQUE_WHATSAPP="+224620000002"
railway variables set PROBLEMATIQUE_CALL="+224620000003"

# Environnement
echo "🌍 Configuration Environnement..."
railway variables set ENVIRONMENT=production
railway variables set DATABASE_URL=sqlite:///chicobot.db

# Déploiement
echo "🚀 Déploiement sur Railway..."
railway up

echo "✅ ChicoBot déployé avec succès !"
echo "🤖 Bot disponible sur: https://railway.app"
echo "📊 Logs: railway logs"
echo "🎯 Envoyez /start à votre bot pour commencer !"
