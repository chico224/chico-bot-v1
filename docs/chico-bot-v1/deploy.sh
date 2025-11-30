#!/bin/bash

# ChicoBot - Script de déploiement automatique
# Compatible: Render, Railway, Oracle Cloud, Docker, VPS

set -e

echo "🇬🇳 Démarrage déploiement ChicoBot pour la Guinée 🇬🇳"

# Vérification Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 non installé"
    exit 1
fi

# Installation dépendances
echo "📦 Installation des dépendances..."
pip3 install -r requirements.txt

# Vérification .env
if [ ! -f .env ]; then
    echo "⚠️  Fichier .env non trouvé, copie depuis .env.example"
    cp .env.example .env
    echo "🔧 Veuillez configurer vos clés dans .env"
    exit 1
fi

# Création répertoires
mkdir -p data logs

# Démarrage du bot
echo "🚀 Démarrage de ChicoBot..."
python3 main.py
