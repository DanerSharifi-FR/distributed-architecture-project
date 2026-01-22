# Impact Service 🎯

**Cerveau du système de détection météo aviation** - Corrèle vols + météo + satellite → calcule "impact" et produit des alertes/rapports.

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌───────────────────┐
│  flight-service │────▶│                  │◀────│  weather-service  │
│   (Bastien)     │     │  IMPACT SERVICE  │     │     (Daner)       │
│                 │     │    (Clovis)      │     │                   │
└─────────────────┘     │                  │     └───────────────────┘
        │               │  - REST API      │              │
        │               │  - GraphQL       │              │
        ▼               │  - MongoDB       │     ┌───────────────────┐
   [RabbitMQ]──────────▶│  - RabbitMQ      │◀────│ satellite-service │
                        │                  │     │    (Thomas)       │
                        └──────────────────┘     └───────────────────┘
```

## Quick Start

### Avec Docker (recommandé)

```bash
# Lancer tout (service + mongo + rabbitmq)
docker-compose up -d

# Voir les logs
docker-compose logs -f impact-service

# Arrêter
docker-compose down
```

### Sans Docker (dev local)

```bash
# Créer un venv
python -m venv venv
source venv/bin/activate  # ou venv\Scripts\activate sur Windows

# Installer les deps
pip install -r requirements.txt

# Copier et configurer .env
cp .env.example .env

# Lancer MongoDB et RabbitMQ (si pas déjà lancés)
# Option: utiliser Docker juste pour ça
docker run -d -p 27017:27017 mongo:7
docker run -d -p 5672:5672 -p 15672:15672 rabbitmq:3-management

# Lancer le service
uvicorn app.main:app --reload --port 8000
```

## Endpoints

### REST API

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| POST | `/api/impacts` | Calculer un impact pour une position |
| GET | `/api/impacts` | Lister les impacts (avec filtres) |
| GET | `/api/impacts/{id}` | Récupérer un impact |
| DELETE | `/api/impacts/{id}` | Supprimer un impact |
| GET | `/api/impacts/flight/{flight_id}` | Impacts d'un vol |
| GET | `/api/impacts/severity/{severity}` | Impacts par sévérité |
| GET | `/api/stats` | Statistiques |

### GraphQL

- **Endpoint**: `/graphql`
- **GraphiQL IDE**: `/graphql` (dans le navigateur)

#### Exemples de queries:

```graphql
# Récupérer un impact
query {
  impact(id: "...") {
    flightId
    severity
    impactScore
    description
    recommendations
    weatherRisk {
      overallScore
      hazards {
        type
        severity
      }
    }
  }
}

# Statistiques
query {
  impactStats {
    totalCount
    criticalCount
    avgImpactScore
  }
}

# Calculer un nouvel impact (mutation)
mutation {
  calculateImpact(position: {
    flightId: "AF1234"
    callsign: "AIR FRANCE 1234"
    latitude: 48.8566
    longitude: 2.3522
    altitude: 10000
  }) {
    id
    severity
    impactScore
    recommendations
  }
}
```

## Tester avec cURL

```bash
# Health check
curl http://localhost:8000/api/health

# Créer un impact
curl -X POST http://localhost:8000/api/impacts \
  -H "Content-Type: application/json" \
  -d '{
    "flight_id": "AF1234",
    "callsign": "AIR FRANCE 1234",
    "latitude": 48.8566,
    "longitude": 2.3522,
    "altitude": 10000,
    "speed": 250,
    "heading": 90
  }'

# Lister les impacts
curl http://localhost:8000/api/impacts

# Impacts critiques
curl http://localhost:8000/api/impacts/severity/critical

# Stats
curl http://localhost:8000/api/stats
```

## Configuration

Variables d'environnement (voir `.env.example`):

| Variable | Description | Default |
|----------|-------------|---------|
| `MONGO_URL` | URL MongoDB | `mongodb://mongo:27017` |
| `MONGO_DB` | Nom de la base | `impact_db` |
| `WEATHER_SERVICE_URL` | URL du weather-service | `http://weather-service:8001` |
| `SATELLITE_SERVICE_URL` | URL du satellite-service | `http://satellite-service:8002` |
| `RABBITMQ_URL` | URL RabbitMQ | `amqp://guest:guest@rabbitmq:5672/` |
| `USE_MOCK_WEATHER` | Utiliser mock météo | `true` |
| `USE_MOCK_SATELLITE` | Utiliser mock satellite | `true` |

## Mode Mock vs Réel

Par défaut, le service utilise des **mocks** pour weather-service et satellite-service, ce qui permet de développer/tester sans avoir les autres services.

Pour passer en mode réel:
1. Mettre `USE_MOCK_WEATHER=false` et/ou `USE_MOCK_SATELLITE=false`
2. S'assurer que les URLs des services sont correctes

## Structure du projet

```
impact-service/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app + lifecycle
│   ├── config.py            # Configuration (pydantic-settings)
│   ├── models/
│   │   ├── impact.py        # Modèles Pydantic + Beanie (MongoDB)
│   │   └── events.py        # Modèles pour events RabbitMQ
│   ├── schemas/
│   │   └── graphql.py       # Schéma GraphQL (Strawberry)
│   ├── services/
│   │   ├── weather_client.py    # Client weather-service (+ mock)
│   │   ├── satellite_client.py  # Client satellite-service (+ mock)
│   │   ├── impact_calculator.py # Logique de calcul d'impact
│   │   └── event_consumer.py    # Consumer RabbitMQ
│   ├── db/
│   │   └── mongodb.py       # Init MongoDB/Beanie
│   └── api/
│       └── rest.py          # Endpoints REST
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## Integration avec les autres services

### Recevoir des positions via REST

Les autres services (ou flight-service) peuvent POST sur `/api/impacts`:

```bash
POST /api/impacts
{
  "flight_id": "...",
  "latitude": ...,
  "longitude": ...,
  "altitude": ...,
  ...
}
```

### Recevoir des positions via RabbitMQ (bonus)

Le service écoute sur la queue `flight_positions`. Format attendu:

```json
{
  "event_type": "flight_position",
  "flight_id": "AF1234",
  "callsign": "AIR FRANCE 1234",
  "latitude": 48.8566,
  "longitude": 2.3522,
  "altitude": 10000,
  "speed": 250,
  "heading": 90,
  "timestamp": "2024-01-15T12:30:00Z"
}
```

### Appels vers weather-service

Quand Daner aura son service prêt, adapter `weather_client.py`:
- URL: `GET /api/weather/risk?lat=...&lon=...&alt=...&time=...`
- Réponse attendue: `{ "overall_score": 0.65, "hazards": [...] }`

### Appels vers satellite-service

Quand Thomas aura son service prêt, adapter `satellite_client.py`:
- URL: `GET /api/satellite/context?lat=...&lon=...&time=...&type=...`
- Réponse attendue: `{ "tile_url": "...", "cloud_coverage": 75.2, ... }`

## Calcul d'impact

Le score d'impact (0-100) est calculé avec ces poids:
- **60%** - Score météo global
- **15%** - Nombre de hazards détectés
- **15%** - Sévérité max des hazards
- **10%** - Couverture nuageuse

Seuils de sévérité:
- **LOW**: < 25
- **MEDIUM**: 25-50
- **HIGH**: 50-75
- **CRITICAL**: > 75

## Documentation API

- **Swagger/OpenAPI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **GraphQL IDE**: http://localhost:8000/graphql
