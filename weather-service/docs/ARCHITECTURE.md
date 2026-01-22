# Architecture

## Current

- Slim 4 PHP app exposing health and readiness endpoints.
- Redis used for readiness checks and future caching.
- Runs behind a container image with `php -S` for local/dev usage.

## Future direction

Planned flow:

- OpenSky service -> telemetry service -> risk service -> weather-service
- weather-service acts as an internal OpenWeather gateway with caching and rate limits
