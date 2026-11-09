#!/bin/bash

# Script de démarrage pour le backend

echo "🚀 Démarrage de la plateforme d'Intelligence Concurrentielle"

# Vérifier si .env existe
if [ ! -f .env ]; then
    echo "⚠️  Fichier .env non trouvé. Copie de env.example..."
    cp env.example .env
    echo "✅ Fichier .env créé. Veuillez le configurer avant de continuer."
    exit 1
fi

# Créer le dossier logs s'il n'existe pas
mkdir -p logs

# Activer l'environnement virtuel si présent
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Lancer l'application
echo "📦 Démarrage de l'API FastAPI..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

