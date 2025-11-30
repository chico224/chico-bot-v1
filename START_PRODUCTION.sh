#!/bin/bash

# 🚀 ChicoBot - Script de Démarrage Production
# Pour la Révolution Guinéenne 🇬🇳

echo "🇬🇳 DÉMARRAGE CHICOBOT - MODE PRODUCTION"
echo "========================================"

# Vérifier Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 non installé. Installation..."
    sudo apt update && sudo apt install python3.11 python3.11-venv python3-pip -y
fi

# Créer environnement virtuel si nécessaire
if [ ! -d "chico_env" ]; then
    echo "📦 Création environnement virtuel..."
    python3.11 -m venv chico_env
fi

# Activer environnement
source chico_env/bin/activate

# Installer dépendances
echo "📦 Installation dépendances..."
pip install -r requirements.txt

# Créer dossiers nécessaires
echo "📁 Création dossiers..."
mkdir -p logs data backups

# Vérifier variables d'environnement
if [ ! -f ".env" ]; then
    echo "⚠️  .env non trouvé. Copie depuis .env.example..."
    cp .env.example .env
    echo "📝 Éditez .env avec vos vraies clés avant de relancer !"
    exit 1
fi

# Initialiser base de données
echo "🗄️  Initialisation base de données..."
python -c "
from src.core.database import DatabaseManager
db = DatabaseManager()
print('✅ Base de données initialisée !')
"

# Test de la voix Chico
echo "🎤 Test voix Chico..."
python examples/chico_personality_demo.py

# Démarrer le bot
echo "🚀 Démarrage ChicoBot..."
echo "📞 Support: +224661920519"
echo "🇬🇳 La Guinée se soulève !"
echo "========================================"

python src/main_bot_chico.py
