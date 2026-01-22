# Technical Deep-Dive

## Overview

The weather-service is an internal OpenWeather gateway focused on proxying and caching One Call 3.0 data. It does not contain flight logic, routing logic for flights, or business rules beyond normalization and caching.

External dependency:
- OpenWeather One Call 3.0 API (`/data/3.0/onecall`).

Internal dependencies:
- Redis for cache and rate limiting.
- Internal auth token via `X-Internal-Token` header for `/v1/*`.

## Request lifecycle (GET /v1/onecall)

Middleware order and flow:
1) RequestIdMiddleware: attaches/propagates `X-Request-Id`.
2) InternalAuthMiddleware: verifies `X-Internal-Token` (skipped if `INTERNAL_TOKEN` empty).
3) RateLimitMiddleware: enforces Redis-based limits on `/v1/onecall`.
4) WeatherController: validates params, consults cache, calls upstream, normalizes, writes cache.

Validation:
- `lat` and `lon` required and constrained to valid ranges.
- `units` is one of `metric|imperial|standard`.
- `lang` is a non-empty string.
- `exclude` is a CSV subset of `current,minutely,hourly,daily,alerts` (sorted and normalized).
- `raw` is `0|1`.

Cache logic:
- Key built from bucketed lat/lon + units + lang + exclude.
- If cache is fresh: respond immediately with cached payload and `meta.cache_hit=true`.
- On miss: call OpenWeather, normalize, cache, respond.
- On upstream failure: serve stale if cached age <= `CACHE_MAX_STALE_SECONDS` and set `meta.stale=true`.

Response metadata:
- `meta.request_id`
- `meta.cache_hit`
- `meta.cache_age_s`
- `meta.upstream_ms`
- `meta.stale`

ASCII sequence (simplified):

```
Client -> RequestIdMiddleware -> InternalAuthMiddleware -> RateLimitMiddleware
      -> WeatherController -> Redis (cache read)
      -> OpenWeatherClient -> OpenWeather API
      <- WeatherNormalizer -> Redis (cache write)
      <- Response (JSON)
```

## Redis: what it stores

### Cache

Key format:
```
weather:v1:lat=<bucketed_lat>:lon=<bucketed_lon>:units=<units>:lang=<lang>:exclude=<exclude>
```

Example:
```
weather:v1:lat=43.60000:lon=1.45000:units=metric:lang=en:exclude=minutely,alerts
```

Value format (JSON):
```
{
  "cached_at": 1710000000,
  "payload": { ...normalized response payload... }
}
```

TTL behavior:
- Stored TTL is `max(CACHE_TTL_SECONDS, CACHE_MAX_STALE_SECONDS)` to support stale-if-error.
- Freshness is determined by `CACHE_TTL_SECONDS`.

Bucket rounding:
- `WEATHER_CACHE_BUCKET_DEG` controls rounding (`round(x/b)*b`).
- Bucketing reduces cache fragmentation for nearby coordinates and improves hit rate.

Key variability:
- `units`, `lang`, and `exclude` are included in the cache key.
- `exclude` is normalized (sorted, lowercased) before key construction.

### Stale-if-error

When stale is served:
- Upstream request fails (transport or non-2xx), and cached entry exists with age <= `CACHE_MAX_STALE_SECONDS`.

Behavior:
- Response uses cached payload.
- `meta.stale=true`
- `meta.cache_hit=true`

### Rate limiting

Rate limits are stored in Redis counters with per-minute windows.

Keys:
```
rate:global:<minute_epoch>
rate:caller:<caller_id>:<minute_epoch>
```

Example:
```
rate:global:28434325
rate:caller:client-123:28434325
```

Window length:
- 60 seconds; window index is `floor(time()/60)`.

Retry-After:
- When limited, response includes `Retry-After` header and `retry_after_s` field.

Other Redis keys:
- None beyond cache and rate limiting.

## Configuration (env vars)

The service loads `.env` for local development (dotenv) and reads values via `Config` helpers. `.env` is git-ignored and should never be committed.

| Env var | Description | Default | Example |
| --- | --- | --- | --- |
| `APP_ENV` | Environment name | `dev` | `prod` |
| `APP_DEBUG` | Enable debug output | `0` | `1` |
| `INTERNAL_TOKEN` | Internal auth token | empty | `abc123...` |
| `OPENWEATHER_API_KEY` | OpenWeather API key | empty | `8f08...` |
| `OPENWEATHER_BASE_URL` | OpenWeather base URL | `https://api.openweathermap.org` | `https://api.openweathermap.org` |
| `OPENWEATHER_CONNECT_TIMEOUT_MS` | Upstream connect timeout (ms) | `1000` | `1500` |
| `OPENWEATHER_TIMEOUT_MS` | Upstream request timeout (ms) | `3000` | `5000` |
| `OPENWEATHER_RETRIES` | Retry count for timeouts/5xx | `2` | `3` |
| `REDIS_URL` | Redis URL | empty | `redis://redis:6379` |
| `CACHE_TTL_SECONDS` | Fresh cache TTL | `600` | `300` |
| `CACHE_MAX_STALE_SECONDS` | Max stale age | `1800` | `900` |
| `WEATHER_CACHE_BUCKET_DEG` | Lat/lon bucket size | `0.05` | `0.1` |
| `RATE_LIMIT_GLOBAL_PER_MIN` | Global rate limit per minute | `300` | `500` |
| `RATE_LIMIT_CALLER_PER_MIN` | Per-caller rate limit per minute | `60` | `100` |
| `WEATHER_SERVICE_BASE_URL` | Test-only: report runner base URL | empty | `http://localhost:8080` |
| `OPENWEATHER_LIVE_LAT` | Test-only: report runner lat | `43.6` | `48.8566` |
| `OPENWEATHER_LIVE_LON` | Test-only: report runner lon | `1.44` | `2.3522` |
| `OPENWEATHER_LIVE_LANG` | Test-only: report runner lang | `en` | `fr` |
| `RUN_LIVE_API` | Test-only: enable live API checks | `0` | `1` |

## Security model

`INTERNAL_TOKEN` is a shared secret for service-to-service calls to `/v1/*`. It must be provided as `X-Internal-Token`.

Generate a token:
```
openssl rand -hex 32
```

Prod vs dev:
- `APP_ENV=prod` requires `INTERNAL_TOKEN` to be set.
- Debug output is suppressed in prod (no stack traces or upstream details).

## Troubleshooting

Common errors:
- `401 UNAUTHORIZED`: missing/invalid `X-Internal-Token`.
- `429 RATE_LIMITED`: per-caller or global limit exceeded.
- `502 UPSTREAM_*`: OpenWeather errors or transport failures.
- `/readyz` `503`: Redis unavailable or `INTERNAL_TOKEN` missing in prod.

Where to look:
- Logs include `extra.request_id` for correlation.
- Use `X-Request-Id` to trace the request end-to-end.

Sample curls:
```
curl -i http://localhost:8080/healthz
curl -i http://localhost:8080/readyz
curl -i -H "X-Internal-Token: $INTERNAL_TOKEN" "http://localhost:8080/v1/onecall?lat=43.6&lon=1.44"
```
