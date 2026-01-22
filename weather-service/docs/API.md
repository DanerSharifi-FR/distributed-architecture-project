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

## Weather (placeholder)

### GET /v1/onecall

Planned endpoint for OpenWeather One Call data. Not implemented yet.
