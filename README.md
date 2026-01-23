# Aviation Weather Impact - Microservices

## Demarrage rapide

```bash
# 1. Cloner le projet
git clone https://github.com/DanerSharifi-FR/distributed-architecture-project.git
cd distributed-architecture-project

# 2. Lancer tous les services (tout est configure, rien a faire)
docker compose up -d --build

# 3. Attendre ~60 secondes que tout demarre
sleep 60

# 4. Tester
curl http://localhost:8000/api/health
# Reponse: {"status":"ok","mongo":true}
```

**C'est tout !** Pas de cle API a configurer, pas de .env a creer.

---

## C'est quoi ce projet ?

Une application backend qui **detecte en temps reel quand un avion traverse des conditions meteo dangereuses**.

### Comment ca marche ?

```
1. On recupere les avions en vol (OpenSky API)
         ↓
2. Pour chaque avion, on recupere la meteo (OpenWeather API)
         ↓
3. On detecte les dangers: orage, vent fort, visibilite, etc.
         ↓
4. On calcule un score d'impact (0-100)
         ↓
5. On genere des images satellite de la zone
         ↓
6. On sauvegarde tout en base de donnees
```

### Exemple de resultat

```json
{
  "flight_id": "SWR96M",
  "callsign": "SWISS",
  "severity": "high",
  "impact_score": 72.5,
  "description": "Vol SWR96M - Dangers: thunderstorm, strong_wind"
}
```

**Score:**
- 0-25 = LOW (conditions normales)
- 25-50 = MEDIUM (vigilance)
- 50-75 = HIGH (conditions difficiles)
- 75-100 = CRITICAL (danger)

---

## Equipe

| Membre | Service | Langage |
|--------|---------|---------|
| Bastien | flight-service | Python (Flask) |
| Clovis | impact-service | Python (FastAPI) |
| Thomas | satellite-service | Kotlin (Spring Boot) |
| Daner | weather-service | PHP (Slim) |

## Architecture

```
                    ┌─────────────────┐
                    │  OpenSky API    │ (API externe - vols temps reel)
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │ flight-service  │ Python/Flask
                    │    (5001)       │
                    └────────┬────────┘
                             │
┌─────────────────┐ ┌────────▼────────┐ ┌─────────────────┐
│ weather-service │ │ impact-service  │ │satellite-service│
│   PHP/Slim      │◄│ Python/FastAPI  │►│ Kotlin/Spring   │
│    (8081)       │ │    (8000)       │ │    (8080)       │
└─────────────────┘ └────────┬────────┘ └────────┬────────┘
        │                    │                   │
        │           ┌────────▼────────┐          │
        │           │    MongoDB      │◄─────────┘
        │           │    (27017)      │
        │           └─────────────────┘
        │
        │           ┌─────────────────┐
        └──────────►│ OpenWeather API │ (API externe - meteo)
                    └─────────────────┘
```

## Services

| Service | Port | Description | API |
|---------|------|-------------|-----|
| **impact-service** | 8000 | Cerveau - calcule les impacts meteo | REST + GraphQL |
| **flight-service** | 5001 | Recupere les vols via OpenSky | REST |
| **satellite-service** | 8080 | Genere images satellite via OpenWeather | REST |
| **weather-service** | 8081 | Proxy meteo avec cache | REST |
| **MongoDB** | 27017 | Base de donnees | - |
| **MinIO** | 9000 | Stockage images | S3 |
| **Redis** | 6379 | Cache weather-service | - |

---

## Demo

### 1. Verifier que tout fonctionne

```bash
# Health check impact-service
curl http://localhost:8000/api/health
# {"status":"ok","mongo":true}

# Health check weather-service
curl http://localhost:8081/healthz
# {"status":"ok"}
```

### 2. Voir les vols en temps reel (flight-service)

```bash
curl http://localhost:5001/flights
```

### 3. Creer des impacts (endpoint principal)

```bash
# Analyse 5 vols et cree des impacts
curl -X POST "http://localhost:8000/api/impacts?limit=5"
```

Resultat:
```json
{
  "analyzed": 5,
  "impacts": [
    {"id": "...", "flight_id": "SWR96M", "severity": "high", "impact_score": 72.5},
    {"id": "...", "flight_id": "AFR123", "severity": "critical", "impact_score": 89.0}
  ]
}
```

### 4. Voir les impacts crees

```bash
curl http://localhost:8000/api/impacts
```

### 5. GraphQL

Ouvrir dans le navigateur: http://localhost:8000/graphql

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

# Creer des impacts
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

Ouvrir: http://localhost:8080/swagger-ui.html

---

## Tests avec Insomnia

Importer le fichier `insomnia-all-services.json` dans Insomnia pour tester toutes les APIs.

---

## Commandes utiles

```bash
# Voir les logs de tous les services
docker compose logs -f

# Logs d'un service specifique
docker compose logs -f impact-service

# Arreter tout
docker compose down

# Tout reconstruire
docker compose down && docker compose up -d --build

# Voir le status
docker compose ps
```

---

## APIs externes utilisees

| API | Usage | Service |
|-----|-------|---------|
| OpenSky Network | Positions avions temps reel | flight-service |
| OpenWeather | Donnees meteo + tuiles satellite | weather-service, satellite-service |

---

## Technologies

| Categorie | Technologies |
|-----------|--------------|
| **Langages** | Python, Kotlin, PHP |
| **Frameworks** | FastAPI, Flask, Spring Boot, Slim |
| **API** | REST, GraphQL (Strawberry) |
| **Base de donnees** | MongoDB |
| **Stockage** | MinIO (S3-compatible) |
| **Cache** | Redis |
| **Conteneurisation** | Docker, Docker Compose |

---

## Ports

| Port | Service |
|------|---------|
| 8000 | impact-service (REST + GraphQL) |
| 5001 | flight-service |
| 8080 | satellite-service |
| 8081 | weather-service |
| 27017 | MongoDB |
| 9000 | MinIO API |
| 8900 | MinIO Console |
| 6379 | Redis |
