# Aviation Weather Impact - Microservices

Application backend qui **détecte en temps réel quand un avion traverse des conditions météo dangereuses**.

---

## Table des matières

- [Démarrage rapide](#démarrage-rapide)
- [Comment ça marche ?](#comment-ça-marche-)
- [Architecture](#architecture)
- [Services](#services)
- [APIs externes et clés API](#apis-externes-et-clés-api)
- [Démo](#démo)
- [Tests avec Insomnia](#tests-avec-insomnia)
- [Équipe](#équipe)
- [Technologies](#technologies)
- [Commandes utiles](#commandes-utiles)

---

## Démarrage rapide

```bash
# 1. Cloner le projet
git clone https://github.com/DanerSharifi-FR/distributed-architecture-project.git
cd distributed-architecture-project

# 2. Lancer tous les services
docker compose up -d --build

# 3. Attendre ~60 secondes que tout démarre
sleep 60

# 4. Vérifier que tout fonctionne
curl http://localhost:8000/api/health
# Réponse: {"status":"ok","mongo":true}
```

> **Note :** Les clés API sont déjà configurées dans `docker-compose.yml`. Voir la section [APIs externes](#apis-externes-et-clés-api) si vous souhaitez utiliser vos propres clés.

---

## Comment ça marche ?

```
1. Récupère les avions en vol        → flight-service (OpenSky API)
         ↓
2. Pour chaque avion, récupère la météo → weather-service (OpenWeather API)
         ↓
3. Détecte les dangers : orage, vent fort, visibilité, etc.
         ↓
4. Calcule un score d'impact (0-100)
         ↓
5. Génère des images satellite         → satellite-service (OpenWeather API)
         ↓
6. Sauvegarde tout en MongoDB
```

### Exemple de résultat

```json
{
  "flight_id": "SWR96M",
  "callsign": "SWISS",
  "severity": "high",
  "impact_score": 72.5,
  "description": "Vol SWR96M - Dangers: thunderstorm, strong_wind"
}
```

### Niveaux de sévérité

| Score | Sévérité | Description |
|-------|----------|-------------|
| 0-25 | LOW | Conditions normales |
| 25-50 | MEDIUM | Vigilance recommandée |
| 50-75 | HIGH | Conditions difficiles |
| 75-100 | CRITICAL | Danger |

---

## Architecture

```
                    ┌─────────────────┐
                    │  OpenSky API    │ (API externe - vols temps réel)
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │ flight-service  │ Python/Flask :5001
                    └────────┬────────┘
                             │
┌─────────────────┐ ┌────────▼────────┐ ┌─────────────────┐
│ weather-service │ │ impact-service  │ │satellite-service│
│   PHP/Slim      │◄│ Python/FastAPI  │►│ Kotlin/Spring   │
│    :8081        │ │    :8000        │ │    :8080        │
└────────┬────────┘ └────────┬────────┘ └────────┬────────┘
         │                   │                   │
         │          ┌────────▼────────┐          │
         │          │    MongoDB      │◄─────────┘
         │          │    :27017       │
         │          └─────────────────┘
         │
         │          ┌─────────────────┐
         └─────────►│ OpenWeather API │ (API externe - météo + satellite)
                    └─────────────────┘
```

---

## Services

| Service | Port | Description | API |
|---------|------|-------------|-----|
| **impact-service** | 8000 | Cerveau - calcule les impacts météo | REST + GraphQL |
| **flight-service** | 5001 | Récupère les vols via OpenSky | REST |
| **satellite-service** | 8080 | Génère images satellite | REST |
| **weather-service** | 8081 | Proxy météo avec cache Redis | REST |
| **MongoDB** | 27017 | Base de données | - |
| **MinIO** | 9000 | Stockage images (S3-compatible) | - |
| **Redis** | 6379 | Cache weather-service | - |

---

## APIs externes et clés API

Ce projet utilise **2 APIs externes**. Les clés sont **déjà configurées** dans `docker-compose.yml`, mais voici comment obtenir vos propres clés si nécessaire :

### 1. OpenSky Network (flight-service)

**Usage :** Récupérer les positions des avions en temps réel.

**Obtenir une clé :**
1. Aller sur https://opensky-network.org/
2. Créer un compte (gratuit)
3. Aller dans Account → API Access
4. Créer un "API Client" (OAuth2)
5. Récupérer le `client_id` et `client_secret`

**Configurer dans `docker-compose.yml` :**
```yaml
flight-service:
  environment:
    - OPENSKY_CLIENT_ID=votre_client_id
    - OPENSKY_CLIENT_SECRET=votre_client_secret
```

### 2. OpenWeather (weather-service et satellite-service)

**Usage :** Récupérer les données météo et les tuiles satellite.

**Obtenir une clé :**
1. Aller sur https://openweathermap.org/api
2. Créer un compte (gratuit)
3. Aller dans "My API Keys"
4. Copier votre API Key (ou en créer une nouvelle)

> **Note :** L'API "One Call" nécessite un abonnement (gratuit avec 1000 appels/jour).

**Configurer dans `docker-compose.yml` :**
```yaml
weather-service:
  environment:
    - OPENWEATHER_API_KEY=votre_api_key

satellite-service:
  environment:
    - SATELLITE_OPENWEATHER_API_KEY=votre_api_key
```

---

## Démo

### 1. Vérifier que tout fonctionne

```bash
# Health check impact-service
curl http://localhost:8000/api/health
# {"status":"ok","mongo":true}

# Health check weather-service
curl http://localhost:8081/healthz
# {"status":"ok"}
```

### 2. Voir les vols en temps réel

```bash
curl http://localhost:5001/flights
```

### 3. Créer des impacts (endpoint principal)

```bash
# Analyse 5 vols et crée des impacts
curl -X POST "http://localhost:8000/api/impacts?limit=5"
```

**Résultat :**
```json
{
  "analyzed": 5,
  "impacts": [
    {"id": "...", "flight_id": "SWR96M", "severity": "high", "impact_score": 72.5},
    {"id": "...", "flight_id": "AFR123", "severity": "critical", "impact_score": 89.0}
  ]
}
```

### 4. Voir les impacts créés

```bash
curl http://localhost:8000/api/impacts
```

### 5. GraphQL

Ouvrir dans le navigateur : http://localhost:8000/graphql

```graphql
# Lister les impacts
{
  impacts(limit: 10) {
    id
    flightId
    callsign
    severity
    impactScore
    description
  }
}

# Créer des impacts
mutation {
  createImpacts(limit: 5) {
    id
    flightId
    severity
    impactScore
  }
}
```

### 6. Swagger satellite-service

Ouvrir : http://localhost:8080/swagger-ui.html

---

## Tests avec Insomnia

1. Ouvrir Insomnia
2. Importer le fichier `insomnia-all-services.json`
3. Suivre le dossier `🎬 DEMO - Workflow complet` pour tester l'application

---

## Équipe

| Membre | Service | Langage | Framework |
|--------|---------|---------|-----------|
| Bastien | flight-service | Python | Flask |
| Clovis | impact-service | Python | FastAPI |
| Thomas | satellite-service | Kotlin | Spring Boot |
| Daner | weather-service | PHP | Slim |

---

## Technologies

| Catégorie | Technologies |
|-----------|--------------|
| **Langages** | Python, Kotlin, PHP |
| **Frameworks** | FastAPI, Flask, Spring Boot, Slim |
| **API** | REST, GraphQL (Strawberry) |
| **Base de données** | MongoDB |
| **Stockage** | MinIO (S3-compatible) |
| **Cache** | Redis |
| **Conteneurisation** | Docker, Docker Compose |

---

## Commandes utiles

```bash
# Lancer tous les services
docker compose up -d --build

# Voir les logs de tous les services
docker compose logs -f

# Logs d'un service spécifique
docker compose logs -f impact-service

# Arrêter tout
docker compose down

# Tout reconstruire
docker compose down && docker compose up -d --build

# Voir le statut des services
docker compose ps
```

---

## Ports

| Port | Service |
|------|---------|
| 8000 | impact-service (REST + GraphQL) |
| 5001 | flight-service |
| 8080 | satellite-service + Swagger |
| 8081 | weather-service |
| 27017 | MongoDB |
| 9000 | MinIO API |
| 8900 | MinIO Console |
| 6379 | Redis |
