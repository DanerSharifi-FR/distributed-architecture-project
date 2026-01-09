# Image légère Python
FROM python:3.12-slim

# Empêche Python de buffer stdout/stderr (logs plus clairs)
ENV PYTHONUNBUFFERED=1

# Dossier de travail
WORKDIR /app

# Copie des dépendances d'abord (cache Docker)
COPY requirements.txt /app/requirements.txt

# Installation deps
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copie du code
COPY app.py /app/app.py

# Port exposé
EXPOSE 5000

# Lancement
CMD ["python", "app.py"]
