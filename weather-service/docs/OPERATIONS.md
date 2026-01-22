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
