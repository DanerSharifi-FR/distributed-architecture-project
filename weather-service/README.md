# Weather Service

Internal OpenWeather gateway microservice. This service focuses on proxying and caching weather data; it does not contain flight logic.

## Quickstart

```bash
docker compose up --build
```

```bash
curl -i http://localhost:8080/healthz
curl -i http://localhost:8080/readyz
```

## Endpoints

- `GET /healthz`
  - Response: `{"status":"ok"}`
- `GET /readyz`
  - Response (ready): `{"status":"ok"}`
  - Response (not ready): `{"status":"error","message":"..."}` with `503`

## Environment variables

- `REDIS_URL`: Redis connection string (required for readiness checks).
- `INTERNAL_TOKEN`: Reserved for future internal auth between services.
- `OPENWEATHER_API_KEY`: Reserved for OpenWeather API authentication.
- `CACHE_TTL_SECONDS`: Reserved for cache TTL configuration.
- `RATE_LIMIT_*`: Reserved for future rate limiting settings.

## Request correlation

- Incoming `X-Request-Id` is propagated to logs and returned in responses.
- If missing, the service generates a UUID-ish value and sets `X-Request-Id`.

## Logging

Logs are emitted in JSON-ish format to stdout. Common fields:
- `level`, `message`, `context`, `datetime`
- `context.request_id` when available

## Troubleshooting

- Redis down: `/readyz` returns `503` with an error message.
- Common Docker issues:
  - Port `8080` already in use: stop the process using it or remap the port.
  - Build failures: ensure Docker has access to the project directory and retry `docker compose up --build`.
