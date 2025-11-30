@echo off
REM ChicoBot - Script Déploiement Railway Automatique Windows

echo 🇬🇳 Déploiement automatique ChicoBot sur Railway 🇬🇳

REM Vérification prérequis
npm --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js/npm non installé
    echo 📦 Installation Node.js : https://nodejs.org/
    pause
    exit /b 1
)

REM Installation CLI Railway
echo 📦 Installation Railway CLI...
npm install -g @railway/cli

REM Login Railway
echo 🔑 Login Railway...
railway login

REM Initialisation projet
echo 🚀 Initialisation projet Railway...
railway init

REM Variables d'environnement obligatoires
echo ⚙️ Configuration variables...

REM Bot Telegram
echo 🤖 Configuration Bot Telegram...
set /p telegram_token="TELEGRAM_BOT_TOKEN: "
railway variables set TELEGRAM_BOT_TOKEN=%telegram_token%

set /p admin_chat_id="TELEGRAM_ADMIN_CHAT_ID: "
railway variables set TELEGRAM_ADMIN_CHAT_ID=%admin_chat_id%

REM Wallet Utilisateur
echo 💰 Configuration Wallet...
set /p wallet_key="WALLET_PRIVATE_KEY: "
railway variables set WALLET_PRIVATE_KEY=%wallet_key%

REM Trading MT5
echo 📊 Configuration Trading MT5...
set /p mt5_login="MT5_LOGIN: "
railway variables set MT5_LOGIN=%mt5_login%

set /p mt5_password="MT5_PASSWORD: "
railway variables set MT5_PASSWORD=%mt5_password%

set /p mt5_server="MT5_SERVER: "
railway variables set MT5_SERVER=%mt5_server%

REM Foundation
echo 🏛️ Configuration Foundation...
set /p foundation_wallet="FOUNDATION_WALLET: "
railway variables set FOUNDATION_WALLET=%foundation_wallet%

REM APIs IA
echo 🧠 Configuration APIs IA...
set /p openai_key="OPENAI_PROJECT_API_KEY: "
railway variables set OPENAI_PROJECT_API_KEY=%openai_key%

set /p gemini_key="GEMINI_API_KEY: "
railway variables set GEMINI_API_KEY=%gemini_key%

REM Sécurité
echo 🔐 Configuration Sécurité...
set /p encryption_key="ENCRYPTION_KEY (32 chars min): "
railway variables set ENCRYPTION_KEY=%encryption_key%

set /p jwt_secret="JWT_SECRET (32 chars min): "
railway variables set JWT_SECRET=%jwt_secret%

REM Support Chico
echo 📞 Configuration Support...
railway variables set CHICO_WHATSAPP="+224620000000"
railway variables set CHICO_CALL="+224620000001"
railway variables set PROBLEMATIQUE_WHATSAPP="+224620000002"
railway variables set PROBLEMATIQUE_CALL="+224620000003"

REM Environnement
echo 🌍 Configuration Environnement...
railway variables set ENVIRONMENT=production
railway variables set DATABASE_URL=sqlite:///chicobot.db

REM Déploiement
echo 🚀 Déploiement sur Railway...
railway up

echo ✅ ChicoBot déployé avec succès !
echo 🤖 Bot disponible sur: https://railway.app
echo 📊 Logs: railway logs
echo 🎯 Envoyez /start à votre bot pour commencer !

pause
