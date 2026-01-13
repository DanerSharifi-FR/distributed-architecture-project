# Aviation Weather Impact - Microservices

Backend microservices qui detecte quand un avion traverse des conditions meteo defavorables.

## Status

| Service | Auteur | Status | Port |
|---------|--------|--------|------|
| flight-service | Bastien | ✅ Termine | 5001 |
| impact-service | Clovis | ✅ Termine | 8000 |
| satellite-service | Thomas | 🟡 A finir | 8080 |
| weather-service | Daner | ❌ Pas commence | 8001 |

## Lancer

```bash
docker compose up -d
curl http://localhost:8000/api/health
curl -X POST "http://localhost:8000/api/analyze-flights?limit=3"
```

## Architecture

```
flight-service --> impact-service --> MongoDB
                         ^
weather-service ---------+
satellite-service -------+
```
