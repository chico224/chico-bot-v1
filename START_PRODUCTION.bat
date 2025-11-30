@echo off
REM 🚀 ChicoBot - Script de Démarrage Production Windows
REM Pour la Révolution Guinéenne 🇬🇳

echo 🇬🇳 DÉMARRAGE CHICOBOT - MODE PRODUCTION
echo ========================================

REM Vérifier Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python non installé. Installez Python 3.11+
    pause
    exit /b 1
)

REM Créer environnement virtuel si nécessaire
if not exist "chico_env" (
    echo 📦 Création environnement virtuel...
    python -m venv chico_env
)

REM Activer environnement
echo 🔄 Activation environnement virtuel...
call chico_env\Scripts\activate.bat

REM Installer dépendances
echo 📦 Installation dépendances...
pip install -r requirements.txt

REM Créer dossiers nécessaires
echo 📁 Création dossiers...
if not exist "logs" mkdir logs
if not exist "data" mkdir data  
if not exist "backups" mkdir backups

REM Vérifier variables d'environnement
if not exist ".env" (
    echo ⚠️  .env non trouvé. Copie depuis .env.example...
    copy .env.example .env
    echo 📝 Éditez .env avec vos vraies clés avant de relancer !
    pause
    exit /b 1
)

REM Initialiser base de données
echo 🗄️  Initialisation base de données...
python -c "from src.core.database import DatabaseManager; db = DatabaseManager(); print('✅ Base de données initialisée !')"

REM Test de la voix Chico
echo 🎤 Test voix Chico...
python examples/chico_personality_demo.py

REM Démarrer le bot
echo 🚀 Démarrage ChicoBot...
echo 📞 Support: +224661920519
echo 🇬🇳 La Guinée se soulève !
echo ========================================

python src/main_bot_chico.py

pause
