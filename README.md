# Aviation Weather Impact - Microservices

Backend microservices qui detecte quand un avion traverse des conditions meteo defavorables.

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
                             ▲
                             │
                    ┌────────┴────────┐
                    │     MinIO       │ (stockage images satellite)
                    │  (9000/8900)    │
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

## Demarrage rapide

### Prerequis

- Docker Desktop installe et demarre
- Git

### Installation

```bash
# 1. Cloner le projet
git clone https://github.com/DanerSharifi-FR/distributed-architecture-project.git
cd distributed-architecture-project

# 2. Lancer tous les services
docker compose up -d

# 3. Attendre ~30 secondes que tout demarre
sleep 30

# 4. Verifier que ca marche
curl http://localhost:8000/api/health
```

### Commandes utiles

```bash
# Voir les logs
docker compose logs -f

# Logs d'un service specifique
docker compose logs -f impact-service

# Arreter tout
docker compose down

# Reconstruire apres modifications
docker compose build --no-cache
docker compose up -d
```

## Demo

### 1. Verifier les services

```bash
curl http://localhost:8000/api/health
# {"status":"ok","mongo":true}
```

### 2. Voir les vols en temps reel

```bash
curl http://localhost:5001/flights | head -100
```

### 3. Analyser des vols (cree impacts + tuiles satellite)

```bash
curl -X POST "http://localhost:8000/api/analyze-flights?limit=5"
```

### 4. Voir les impacts crees

```bash
curl http://localhost:8000/api/impacts
```

### 5. Creer un impact manuellement

```bash
curl -X POST http://localhost:8000/api/impacts \
  -H "Content-Type: application/json" \
  -d '{
    "flight_id": "AF1234",
    "callsign": "AIR FRANCE",
    "latitude": 48.8566,
    "longitude": 2.3522,
    "altitude": 35000
  }'
```

### 6. GraphQL (impact-service)

Ouvrir dans le navigateur: http://localhost:8000/graphql

```graphql
# Query - lister les impacts
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

# Mutation - analyser des vols
mutation {
  analyzeFlights(limit: 5) {
    id
    flightId
    severity
  }
}
```

### 7. Swagger satellite-service

Ouvrir: http://localhost:8080/swagger-ui.html

## APIs externes utilisees

### OpenSky Network (flight-service)
- **URL**: https://opensky-network.org/api
- **Usage**: Positions des avions en temps reel
- **Gratuit**: Oui (avec limites)

### OpenWeather (weather-service + satellite-service)
- **URL**: https://openweathermap.org/api
- **Usage**: Donnees meteo + tuiles satellite
- **Cle API**: Necessaire (gratuit avec compte)

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

## Structure du projet

```
distributed-architecture-project/
├── docker-compose.yml          # Orchestration de tous les services
├── README.md                   # Ce fichier
├── insomnia-all-services.yaml  # Collection Insomnia pour tests
│
├── impact-service/             # Clovis - Python/FastAPI
│   ├── app/
│   │   ├── main.py
│   │   ├── api/rest.py
│   │   ├── schemas/graphql.py
│   │   └── services/
│   ├── Dockerfile
│   └── requirements.txt
│
├── flight-service/             # Bastien - Python/Flask
│   ├── app.py
│   └── Dockerfile
│
├── satellite-service/          # Thomas - Kotlin/Spring Boot
│   ├── src/main/kotlin/
│   ├── pom.xml
│   └── Dockerfile
│
└── weather-service/            # Daner - PHP/Slim
    ├── src/
    ├── public/
    └── docker/Dockerfile
```

## Tests avec Insomnia

Importer le fichier `insomnia-all-services.yaml` dans Insomnia pour tester toutes les APIs.

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
