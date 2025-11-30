@echo off
REM ChicoBot - Script de déploiement automatique Windows
REM Compatible: Render, Railway, Oracle Cloud, Docker, VPS

echo 🇬🇳 Démarrage déploiement ChicoBot pour la Guinée 🇬🇳

REM Vérification Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python non installé
    pause
    exit /b 1
)

REM Installation dépendances
echo 📦 Installation des dépendances...
pip install -r requirements.txt

REM Vérification .env
if not exist .env (
    echo ⚠️  Fichier .env non trouvé, copie depuis .env.example
    copy .env.example .env
    echo 🔧 Veuillez configurer vos clés dans .env
    pause
    exit /b 1
)

REM Création répertoires
if not exist data mkdir data
if not exist logs mkdir logs

REM Démarrage du bot
echo 🚀 Démarrage de ChicoBot...
python main.py

pause
