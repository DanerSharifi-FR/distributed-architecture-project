# API

## Health

### GET /healthz

Request:

```bash
curl -i http://localhost:8080/healthz
```

Response:

```json
{"status":"ok"}
```

### GET /readyz

Request:

```bash
curl -i http://localhost:8080/readyz
```

Response (ready):

```json
{"status":"ok"}
```

Response (not ready):

```json
{"status":"error","message":"..."}
```

## Weather

### GET /v1/onecall

Proxy to OpenWeather One Call 3.0 with caching and schema normalization.

Auth:

- `X-Internal-Token: <token>` is required for `/v1/*` when `INTERNAL_TOKEN` is set.

Request:

```bash
curl -i \
  -H "X-Internal-Token: $INTERNAL_TOKEN" \
  "http://localhost:8080/v1/onecall?lat=48.8566&lon=2.3522&units=metric&lang=en&exclude=minutely,alerts&raw=0"
```

Query parameters:

- `lat` (required): float, -90..90
- `lon` (required): float, -180..180
- `units` (optional): `metric|imperial|standard` (default `metric`)
- `lang` (optional): language code (default `en`)
- `exclude` (optional): csv subset of `current,minutely,hourly,daily,alerts`
- `raw` (optional): `0|1` (default `0`)

Response shape:

```json
{
  "meta": {
    "request_id": "uuid",
    "cache_hit": false,
    "cache_age_s": null,
    "upstream_ms": 132,
    "stale": false
  },
  "location": {
    "lat": 48.8566,
    "lon": 2.3522
  },
  "current": {},
  "hourly": [],
  "alerts": [],
  "raw": null
}
```

Errors:

- `400 VALIDATION_ERROR`
- `401 UNAUTHORIZED`
- `429 RATE_LIMITED`
- `502 UPSTREAM_AUTH_ERROR` (OpenWeather One Call subscription/product not enabled or access denied)
- `502 UPSTREAM_RATE_LIMIT`
- `502 UPSTREAM_ERROR`
- `500 INTERNAL_ERROR`

Error codes:

| Code | Meaning |
| --- | --- |
| VALIDATION_ERROR | Request parameters invalid |
| UNAUTHORIZED | Missing or invalid internal token |
| RATE_LIMITED | Rate limit exceeded |
| UPSTREAM_AUTH_ERROR | OpenWeather access denied |
| UPSTREAM_RATE_LIMIT | OpenWeather rate limit exceeded |
| UPSTREAM_ERROR | Upstream error |
| INTERNAL_ERROR | Unhandled error |

Example request/response:

```bash
curl -i \
  -H "X-Internal-Token: $INTERNAL_TOKEN" \
  "http://localhost:8080/v1/onecall?lat=43.6&lon=1.44"
```

```http
HTTP/1.1 200 OK
Content-Type: application/json
X-Request-Id: 1234
```

Example 429:

```json
{
  "error_code": "RATE_LIMITED",
  "message": "Too many requests",
  "request_id": "uuid",
  "retry_after_s": 12
}
```
