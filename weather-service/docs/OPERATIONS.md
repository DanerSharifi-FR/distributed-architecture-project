# Operations

## Health and readiness

- `/healthz` indicates the process is up and responding.
- `/readyz` indicates dependencies are reachable (Redis).

## Metrics (placeholder)

- Prometheus metrics endpoint to be added in the future.
- Request/response latency, error rates, cache hit ratio.

## Runbook notes

- Copy `.env.example` to `.env` for local runs and set required values.
- Never commit `.env` or secrets; use CI secret management for deployments.
- If `/readyz` is failing, confirm Redis connectivity and credentials.
- Check `REDIS_URL` is set in the container environment.
- Inspect logs for `request_id` to trace a request end-to-end.

## Caching behavior

- Weather responses are cached by bucketed coordinates, units, lang, and exclude.
- Fresh cache TTL is controlled by `CACHE_TTL_SECONDS`.
- Stale cache responses are served on upstream failure while `cache_age_s <= CACHE_MAX_STALE_SECONDS`.

## Rate limiting

- `/v1/onecall` is rate limited via Redis.
- `RATE_LIMIT_GLOBAL_PER_MIN` controls the global ceiling.
- `RATE_LIMIT_CALLER_PER_MIN` controls per-caller limits (X-Caller-Id or client IP).

## Readiness in prod

- When `APP_ENV=prod`, `INTERNAL_TOKEN` must be set or `/readyz` returns `503`.

## Logging and request correlation

- Incoming `X-Request-Id` is echoed in responses and included in logs.
- Look for `extra.request_id` in JSON logs to trace a request.
