# Weather Service

Internal OpenWeather gateway microservice. This service focuses on proxying and caching weather data; it does not contain flight logic.

## Quickstart

```bash
cp .env.example .env
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
- `GET /v1/onecall`
  - Internal OpenWeather One Call 3.0 proxy with caching.
  - Requires `X-Internal-Token` header when `INTERNAL_TOKEN` is set.

## Install & Run

Prereqs:
- Docker + Docker Compose, or
- PHP 8.3+ + Composer + Redis

Local (Docker) quickstart:

```bash
cp .env.example .env
```

Fill required values:
- `OPENWEATHER_API_KEY` (required)
- `INTERNAL_TOKEN` (required in prod; recommended always)

```bash
docker compose up --build
```

```bash
curl -i http://localhost:8080/healthz
curl -i http://localhost:8080/readyz
curl -i -H "X-Internal-Token: $INTERNAL_TOKEN" "http://localhost:8080/v1/onecall?lat=43.6&lon=1.44"
```

Local (no Docker):

```bash
composer install
```

Start Redis, then:

```bash
export OPENWEATHER_API_KEY=...
export INTERNAL_TOKEN=...
php -S 0.0.0.0:8080 -t public
```

Troubleshooting:
- `401` => missing/invalid `X-Internal-Token`
- `429` => rate limit exceeded
- `502` => upstream issue (check OpenWeather subscription/activation + logs)
- `/readyz` `503` => Redis down or `INTERNAL_TOKEN` missing in prod

## Environment variables

Create a local `.env` from `.env.example` and fill in values. Never commit secrets; use CI secret stores for production.

- `REDIS_URL`: Redis connection string (required for caching and readiness checks).
- `INTERNAL_TOKEN`: Internal auth token for `/v1/*` routes (empty disables checks).
- `OPENWEATHER_API_KEY`: OpenWeather API key.
- `OPENWEATHER_BASE_URL`: Base URL for OpenWeather (default `https://api.openweathermap.org`).
- `OPENWEATHER_CONNECT_TIMEOUT_MS`: Upstream connect timeout in milliseconds.
- `OPENWEATHER_TIMEOUT_MS`: Upstream timeout in milliseconds.
- `OPENWEATHER_RETRIES`: Upstream retry count for timeouts/5xx responses.
- `CACHE_TTL_SECONDS`: Cache TTL for fresh responses.
- `CACHE_MAX_STALE_SECONDS`: Maximum age for stale-if-error responses.
- `WEATHER_CACHE_BUCKET_DEG`: Lat/lon bucket size for cache keys.
- `RATE_LIMIT_*`: Reserved for future rate limiting settings.

`.env` is loaded for local development via `vlucas/phpdotenv`. Any already-defined environment variables take precedence over `.env` values.

## Request correlation

- Incoming `X-Request-Id` is propagated to logs and returned in responses.
- If missing, the service generates a UUID-ish value and sets `X-Request-Id`.

## Logging

Logs are emitted in JSON-ish format to stdout. Common fields:
- `level`, `message`, `context`, `datetime`
- `extra.request_id` when available

## Caching

- Responses are cached by bucketed lat/lon, units, lang, and exclude values.
- If the upstream API fails, cached responses within `CACHE_MAX_STALE_SECONDS` are returned with `meta.stale=true`.

## Production notes

- `APP_ENV=prod` requires a non-empty `INTERNAL_TOKEN`; readiness will report `503` if missing.
- Rate limiting uses Redis: `RATE_LIMIT_GLOBAL_PER_MIN` and `RATE_LIMIT_CALLER_PER_MIN`.
- All errors are returned as JSON. In dev, responses may include a `debug` object; in prod, debug details are omitted.

## Security

- `INTERNAL_TOKEN` is a shared secret for service-to-service auth on `/v1/*`.
- Never commit `.env` files or secrets.
- In production, `APP_ENV=prod` requires `INTERNAL_TOKEN` to be set.

## Token generation

```bash
openssl rand -hex 32
```

Alternative:

```bash
python -c 'import secrets; print(secrets.token_hex(32))'
```

Add to `.env`:

```
INTERNAL_TOKEN=<generated>
```

## Helper scripts

- `scripts/gen-token.sh`: prints a token and a sample `.env` line.
- `scripts/setup-env.sh`: copies `.env.example` to `.env` if missing.

## Technical deep-dive

See `docs/TECHNICAL.md` for request flow, Redis usage, and configuration details.

## API documentation

- `/docs` (Swagger UI)
- `/openapi.yaml` (OpenAPI 3.0 spec)

## Documentation index

- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- [docs/API.md](docs/API.md)
- [docs/DECISIONS.md](docs/DECISIONS.md)
- [docs/OPERATIONS.md](docs/OPERATIONS.md)
- [docs/TECHNICAL.md](docs/TECHNICAL.md)
- [docs/openapi.yaml](docs/openapi.yaml)

## Troubleshooting

- Redis down: `/readyz` returns `503` with an error message.
- One Call 3.0 access: `401/403` from `/v1/onecall` means the OpenWeather One Call subscription/product is not enabled for the API key.
- Common Docker issues:
  - Port `8080` already in use: stop the process using it or remap the port.
  - Build failures: ensure Docker has access to the project directory and retry `docker compose up --build`.
