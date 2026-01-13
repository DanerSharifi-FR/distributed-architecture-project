# Impact Service

Cerveau du systeme - calcule l'impact meteo des vols.

## Quick Start

```bash
docker compose up -d
```

## API

### REST (http://localhost:8000/docs)

```bash
# Health
curl http://localhost:8000/api/health

# Analyser les vols
curl -X POST "http://localhost:8000/api/analyze-flights?limit=5"

# Creer un impact
curl -X POST http://localhost:8000/api/impacts \
  -d '{"flight_id":"TEST","latitude":48.8,"longitude":2.3,"altitude":10000}'

# Liste
curl http://localhost:8000/api/impacts

# Stats
curl http://localhost:8000/api/stats
```

### GraphQL (http://localhost:8000/graphql)

```graphql
mutation { analyzeFlightsFromService(limit: 5) { flightId severity impactScore } }
query { impacts { flightId severity impactScore } }
```

## Env

- `MONGO_URL` - MongoDB URL
- `FLIGHT_SERVICE_URL` - URL du flight-service
- `USE_MOCK_WEATHER=true` - Mock weather (Daner pas pret)
- `USE_MOCK_SATELLITE=true` - Mock satellite (Thomas pas pret)
