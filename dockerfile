# Image de base légère avec Python 3.11
FROM python:3.11-slim

# Créer un utilisateur non-root pour sécurité
RUN useradd -m appuser
USER appuser

# Dossier de travail
WORKDIR /app

# Copier les fichiers du projet
COPY requirements.txt .
COPY main.py .
COPY config/ config/
COPY core/ core/
COPY handlers/ handlers/
COPY services/ services/
COPY tasks/ tasks/
COPY .env.example .env  # Optionnel, mais utile pour exemple

# Installer les dépendances (avec cache pour accélérer)
RUN pip install --no-cache-dir -r requirements.txt

# Exposer le port (pas obligatoire pour bot Telegram, mais Back4app aime en avoir un)
EXPOSE 8080

# Commande de lancement
CMD ["python", "main.py"]
