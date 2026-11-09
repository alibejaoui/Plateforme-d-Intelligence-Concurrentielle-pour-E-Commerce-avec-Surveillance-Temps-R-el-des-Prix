@echo off
REM Script de démarrage pour Windows

echo 🚀 Démarrage de la plateforme d'Intelligence Concurrentielle

REM Vérifier si .env existe
if not exist .env (
    echo ⚠️  Fichier .env non trouvé. Copie de env.example...
    copy env.example .env
    echo ✅ Fichier .env créé. Veuillez le configurer avant de continuer.
    pause
    exit /b 1
)

REM Créer le dossier logs s'il n'existe pas
if not exist logs mkdir logs

REM Activer l'environnement virtuel si présent
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)

REM Lancer l'application
echo 📦 Démarrage de l'API FastAPI...
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

