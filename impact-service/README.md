# Impact Service

Service de calcul d'impact météo pour les vols. Détecte quand un avion traverse des conditions météo défavorables.

## Stack

| Technologie | Rôle |
|-------------|------|
| **FastAPI** | Framework web async |
| **Strawberry** | API GraphQL |
| **Motor** | Driver MongoDB async |
| **MongoDB** | Base de données |
| **Docker** | Conteneurisation |

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    impact-service                        │
│                     (port 8000)                          │
├─────────────────────────────────────────────────────────┤
│                                                         │
│   REST API (/api/*)          GraphQL (/graphql)         │
│        │                          │                     │
│        └──────────┬───────────────┘                     │
│                   ▼                                     │
│            Impact Calculator                            │
│                   │                                     │
│         ┌────────┼────────┐                            │
│         ▼        ▼        ▼                            │
│    Weather   Satellite  Flight                         │
│    Client    Client     Client                         │
│      │          │          │                           │
│      ▼          ▼          ▼                           │
│  weather-   satellite-  flight-                        │
│  service    service     service                        │
│  (8081)     (8080)      (5001)                         │
│                                                         │
├─────────────────────────────────────────────────────────┤
│                   Motor (driver)                        │
│                       │                                 │
│                       ▼                                 │
│       MongoDB (collection: 'impact')                    │
│            (partagé avec satellite-service)             │
└─────────────────────────────────────────────────────────┘
```

## Structure des fichiers

```
impact-service/
├── app/
│   ├── main.py              # Point d'entrée FastAPI
│   ├── config.py            # Configuration (env vars)
│   ├── api/
│   │   └── rest.py          # Endpoints REST
│   ├── schemas/
│   │   └── graphql.py       # Schema GraphQL (Strawberry)
│   ├── models/
│   │   └── impact.py        # Modèles Pydantic
│   ├── services/
│   │   ├── impact_calculator.py  # Logique métier
│   │   ├── weather_client.py     # Client weather (mock)
│   │   ├── satellite_client.py   # Client satellite (mock)
│   │   └── flight_client.py      # Client flight-service
│   └── db/
│       └── mongodb.py       # Connexion MongoDB (Motor)
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## Lancement

### Avec Docker (recommandé)

```bash
# Depuis la racine du projet
docker compose up -d

# Vérifier les logs
docker compose logs -f impact-service
```

### Sans Docker (dev)

```bash
cd impact-service

# Installer les dépendances
pip install -r requirements.txt

# Lancer MongoDB
docker run -d -p 27017:27017 mongo

# Lancer le service
uvicorn app.main:app --reload --port 8000
```

## API REST

Base URL: `http://localhost:8000/api`

### Endpoints

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/impacts` | Créer un impact |
| `GET` | `/impacts` | Lister les impacts |
| `GET` | `/impacts/{id}` | Récupérer un impact |
| `DELETE` | `/impacts/{id}` | Supprimer un impact |
| `POST` | `/analyze-flights` | Analyser les vols depuis flight-service |
| `GET` | `/stats` | Statistiques |

### Exemples

**Créer un impact:**
```bash
curl -X POST http://localhost:8000/api/impacts \
  -H "Content-Type: application/json" \
  -d '{
    "flight_id": "AF123",
    "callsign": "AIR FRANCE",
    "latitude": 48.8566,
    "longitude": 2.3522,
    "altitude": 35000
  }'
```

**Lister les impacts:**
```bash
curl http://localhost:8000/api/impacts
```

**Analyser les vols en temps réel:**
```bash
curl -X POST "http://localhost:8000/api/analyze-flights?limit=5"
```

## API GraphQL

URL: `http://localhost:8000/graphql`

### Interface GraphiQL

Ouvrir dans le navigateur: http://localhost:8000/graphql

### Queries

```graphql
# Lister les impacts
{
  impacts {
    id
    flightId
    severity
    impactScore
    description
  }
}

# Récupérer un impact par ID
{
  impact(id: "xxx") {
    id
    flightId
    severity
  }
}

# Stats
{
  stats
}
```

### Mutations

```graphql
# Calculer un impact manuellement
mutation {
  calculateImpact(position: {
    flightId: "AF123"
    latitude: 48.8
    longitude: 2.3
    altitude: 35000
  }) {
    id
    severity
    impactScore
  }
}

# Analyser les vols depuis flight-service
mutation {
  analyzeFlightsFromService(limit: 5) {
    id
    flightId
    severity
    impactScore
  }
}
```

## Configuration

Variables d'environnement (dans `.env` ou docker-compose):

| Variable | Default | Description |
|----------|---------|-------------|
| `MONGO_URL` | `mongodb://mongo:27017` | URL MongoDB |
| `MONGO_DB` | `impact_db` | Nom de la base |
| `FLIGHT_SERVICE_URL` | `http://flight-service:5000` | URL du flight-service |
| `USE_MOCK_WEATHER` | `true` | Utiliser les mocks weather |
| `USE_MOCK_SATELLITE` | `true` | Utiliser les mocks satellite |

## Modèle de données

### Impact

```json
{
  "_id": "ObjectId",
  "flight_id": "AF123",
  "callsign": "AIR FRANCE",
  "position": {
    "latitude": 48.8566,
    "longitude": 2.3522,
    "altitude": 35000,
    "timestamp": "2024-01-15T10:30:00Z"
  },
  "weather_risk": {
    "overall_score": 0.75,
    "hazards": [
      {"type": "thunderstorm", "severity": 0.8},
      {"type": "icing", "severity": 0.5}
    ]
  },
  "severity": "high",
  "impact_score": 72.5,
  "description": "Vol AF123 - Dangers: thunderstorm, icing",
  "recommendations": ["Vigilance"],
  "created_at": "2024-01-15T10:30:00Z"
}
```

### Severity levels

| Score | Severity |
|-------|----------|
| 0-25 | `low` |
| 25-50 | `medium` |
| 50-75 | `high` |
| 75-100 | `critical` |

## Services externes

### flight-service (Bastien) ✅
- Port: 5001
- Endpoint: `GET /flights`
- Status: **Intégré** - Récupère les vols en temps réel via OpenSky

### weather-service (Daner) ✅
- Port: 8081
- Endpoint: `GET /v1/onecall?lat=...&lon=...`
- Status: **Intégré** (mais utilise mock par défaut, set `USE_MOCK_WEATHER=false` pour activer)

### satellite-service (Thomas) ✅
- Port: 8080
- Endpoint: `PUT /satellites/tiles/impacts/{impactId}`
- Status: **Intégré** - Génère des tuiles satellite automatiquement après chaque impact

## Flow d'intégration

```
1. POST /api/impacts ou POST /api/analyze-flights
   │
   ├─► Calcule l'impact météo (weather-service ou mock)
   │
   ├─► Sauvegarde en MongoDB (collection 'impact')
   │
   └─► Déclenche satellite-service (PUT /satellites/tiles/impacts/{id})
       │
       └─► satellite-service lit l'impact depuis MongoDB
           et génère les tuiles via OpenWeather
```

## Test rapide

```bash
# 1. Lancer tous les services
docker compose up -d

# 2. Créer un impact
curl -X POST http://localhost:8000/api/impacts \
  -H "Content-Type: application/json" \
  -d '{"flight_id": "TEST001", "latitude": 48.8, "longitude": 2.3, "altitude": 35000}'

# 3. Analyser des vols réels
curl -X POST "http://localhost:8000/api/analyze-flights?limit=5"

# 4. Voir les impacts
curl http://localhost:8000/api/impacts
```