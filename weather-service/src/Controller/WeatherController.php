<?php

declare(strict_types=1);

namespace App\Controller;

use App\Config;
use App\Service\OpenWeatherClient;
use App\Service\OpenWeatherException;
use App\Service\WeatherCache;
use App\Service\WeatherNormalizer;
use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\ServerRequestInterface;
use Psr\Log\LoggerInterface;

final class WeatherController
{
    private const UNITS_ALLOWED = ['metric', 'imperial', 'standard'];
    private const EXCLUDE_ALLOWED = ['current', 'minutely', 'hourly', 'daily', 'alerts'];

    public function __construct(
        private readonly WeatherCache $cache,
        private readonly OpenWeatherClient $client,
        private readonly WeatherNormalizer $normalizer,
        private readonly LoggerInterface $logger
    ) {
    }

    public function onecall(ServerRequestInterface $request, ResponseInterface $response): ResponseInterface
    {
        $requestId = (string) $request->getAttribute('request_id');
        $query = $request->getQueryParams();

        [$errors, $normalized] = $this->validate($query);
        if ($errors !== []) {
            return $this->json($response, 400, [
                'error_code' => 'VALIDATION_ERROR',
                'message' => 'Validation failed',
                'details' => $errors,
                'request_id' => $requestId,
            ]);
        }

        $lat = $normalized['lat'];
        $lon = $normalized['lon'];
        $units = $normalized['units'];
        $lang = $normalized['lang'];
        $exclude = $normalized['exclude'];
        $includeRaw = $normalized['raw'];
        $upstreamUrlSanitized = $this->client->buildOneCallSanitizedUrl($lat, $lon, $units, $lang, $exclude);

        $cacheKey = WeatherCache::buildKey(
            $lat,
            $lon,
            $units,
            $lang,
            $exclude,
            $this->cache->getBucketDegrees()
        );

        $cacheEntry = $this->cache->get($cacheKey);
        if ($cacheEntry !== null && $this->cache->isFresh((int) $cacheEntry['cached_at'])) {
            $payload = $this->normalizer->applyRawPreference($cacheEntry['payload'], $includeRaw);

            return $this->respondSuccess($response, $requestId, $lat, $lon, $payload, [
                'cache_hit' => true,
                'cache_age_s' => $this->cache->ageSeconds((int) $cacheEntry['cached_at']),
                'upstream_ms' => null,
                'stale' => false,
            ]);
        }

        try {
            $this->logger->debug('OpenWeather upstream request', [
                'request_id' => $requestId,
                'url' => $upstreamUrlSanitized,
            ]);

            $upstream = $this->client->fetchOneCall($lat, $lon, $units, $lang, $exclude);
            if (($upstream['ok'] ?? false) !== true) {
                return $this->handleUpstreamFailure(
                    $request,
                    $response,
                    $lat,
                    $lon,
                    $cacheEntry,
                    $includeRaw,
                    $upstream,
                    $upstreamUrlSanitized
                );
            }

            $normalizedPayload = $this->normalizer->normalize($upstream['payload'], true);
            $this->cache->set($cacheKey, $normalizedPayload);
            $payload = $this->normalizer->applyRawPreference($normalizedPayload, $includeRaw);

            return $this->respondSuccess($response, $requestId, $lat, $lon, $payload, [
                'cache_hit' => false,
                'cache_age_s' => null,
                'upstream_ms' => $upstream['upstream_ms'],
                'stale' => false,
            ]);
        } catch (OpenWeatherException $exception) {
            if ($cacheEntry !== null && $this->cache->isWithinMaxStale((int) $cacheEntry['cached_at'])) {
                $payload = $this->normalizer->applyRawPreference($cacheEntry['payload'], $includeRaw);

                return $this->respondSuccess($response, $requestId, $lat, $lon, $payload, [
                    'cache_hit' => true,
                    'cache_age_s' => $this->cache->ageSeconds((int) $cacheEntry['cached_at']),
                    'upstream_ms' => null,
                    'stale' => true,
                ]);
            }

            $this->logger->warning('OpenWeather upstream error', [
                'request_id' => $requestId,
                'error' => $exception->getMessage(),
                'url' => $upstreamUrlSanitized,
            ]);

            $debug = null;
            if ($this->shouldIncludeDebug()) {
                $debug = [
                    'upstream_url_sanitized' => $upstreamUrlSanitized,
                    'status' => null,
                    'error' => sprintf('%s: %s', $exception::class, $exception->getMessage()),
                    'body_snippet' => null,
                    'upstream_ms' => null,
                ];
            }

            return $this->json($response, 502, array_filter([
                'error_code' => 'UPSTREAM_ERROR',
                'message' => 'Upstream service unavailable',
                'request_id' => $requestId,
                'debug' => $debug,
            ]));
        } catch (\Throwable $exception) {
            $this->logger->error('Weather controller error', [
                'request_id' => $requestId,
                'error' => $exception->getMessage(),
            ]);

            return $this->json($response, 500, [
                'error_code' => 'INTERNAL_ERROR',
                'message' => 'Unexpected server error',
                'request_id' => $requestId,
            ]);
        }
    }

    private function handleUpstreamFailure(
        ServerRequestInterface $request,
        ResponseInterface $response,
        float $lat,
        float $lon,
        ?array $cacheEntry,
        bool $includeRaw,
        array $upstream,
        string $upstreamUrlSanitized
    ): ResponseInterface {
        $requestId = (string) $request->getAttribute('request_id');
        $status = (int) ($upstream['status'] ?? 0);

        if ($cacheEntry !== null && $this->cache->isWithinMaxStale((int) $cacheEntry['cached_at'])) {
            $payload = $this->normalizer->applyRawPreference($cacheEntry['payload'], $includeRaw);

            return $this->respondSuccess($response, $requestId, $lat, $lon, $payload, [
                'cache_hit' => true,
                'cache_age_s' => $this->cache->ageSeconds((int) $cacheEntry['cached_at']),
                'upstream_ms' => null,
                'stale' => true,
            ]);
        }

        $debug = null;
        if ($this->shouldIncludeDebug()) {
            $debug = [
                'upstream_url_sanitized' => $upstreamUrlSanitized,
                'status' => $status,
                'error' => (string) ($upstream['error_message'] ?? ''),
                'body_snippet' => (string) ($upstream['body_snippet'] ?? ''),
                'upstream_ms' => $upstream['upstream_ms'] ?? null,
            ];
        }

        $this->logger->warning('OpenWeather upstream failure', [
            'request_id' => $requestId,
            'status' => $status,
            'body_snippet' => (string) ($upstream['body_snippet'] ?? ''),
            'upstream_ms' => $upstream['upstream_ms'] ?? null,
            'url' => $upstreamUrlSanitized,
        ]);

        if ($status === 401 || $status === 403) {
            return $this->json($response, 502, array_filter([
                'error_code' => 'UPSTREAM_AUTH_ERROR',
                'message' => 'OpenWeather One Call API access denied (check subscription / product activation)',
                'request_id' => $requestId,
                'debug' => $debug,
            ]));
        }

        if ($status === 429) {
            return $this->json($response, 502, array_filter([
                'error_code' => 'UPSTREAM_RATE_LIMIT',
                'message' => 'OpenWeather One Call API rate limit exceeded',
                'request_id' => $requestId,
                'debug' => $debug,
            ]));
        }

        return $this->json($response, 502, array_filter([
            'error_code' => 'UPSTREAM_ERROR',
            'message' => 'Upstream service unavailable',
            'request_id' => $requestId,
            'debug' => $debug,
        ]));
    }

    private function shouldIncludeDebug(): bool
    {
        if (Config::envBool('APP_DEBUG', false)) {
            return true;
        }

        return Config::envString('APP_ENV', '') === 'dev';
    }

    private function respondSuccess(
        ResponseInterface $response,
        string $requestId,
        float $lat,
        float $lon,
        array $payload,
        array $meta
    ): ResponseInterface {
        $body = [
            'meta' => array_merge(['request_id' => $requestId], $meta),
            'location' => [
                'lat' => $lat,
                'lon' => $lon,
            ],
        ];

        $body = array_merge($body, $payload);

        return $this->json($response, 200, $body);
    }

    public function debugOnecall(ServerRequestInterface $request, ResponseInterface $response): ResponseInterface
    {
        [$errors, $normalized] = $this->validate($request->getQueryParams());
        if ($errors !== []) {
            return $this->json($response, 400, [
                'error_code' => 'VALIDATION_ERROR',
                'message' => 'Validation failed',
                'details' => $errors,
                'request_id' => (string) $request->getAttribute('request_id'),
            ]);
        }

        $lat = $normalized['lat'];
        $lon = $normalized['lon'];
        $units = $normalized['units'];
        $lang = $normalized['lang'];
        $exclude = $normalized['exclude'];

        $upstreamUrlSanitized = $this->client->buildOneCallSanitizedUrl($lat, $lon, $units, $lang, $exclude);

        try {
            $this->logger->debug('OpenWeather upstream debug request', [
                'request_id' => (string) $request->getAttribute('request_id'),
                'url' => $upstreamUrlSanitized,
            ]);

            $upstream = $this->client->fetchOneCall($lat, $lon, $units, $lang, $exclude);

            return $this->json($response, 200, [
                'ok' => (bool) ($upstream['ok'] ?? false),
                'status' => (int) ($upstream['status'] ?? 200),
                'upstream_url_sanitized' => $upstreamUrlSanitized,
                'body_snippet' => (string) ($upstream['body_snippet'] ?? ''),
                'error' => (string) ($upstream['error_message'] ?? ''),
            ]);
        } catch (OpenWeatherException $exception) {
            return $this->json($response, 200, [
                'ok' => false,
                'status' => null,
                'upstream_url_sanitized' => $upstreamUrlSanitized,
                'body_snippet' => '',
                'error' => sprintf('%s: %s', $exception::class, $exception->getMessage()),
            ]);
        }
    }

    private function validate(array $query): array
    {
        $errors = [];
        $normalized = [];

        $latRaw = $query['lat'] ?? null;
        $lonRaw = $query['lon'] ?? null;

        if ($latRaw === null || $latRaw === '') {
            $errors['lat'] = 'lat is required';
        } elseif (filter_var($latRaw, FILTER_VALIDATE_FLOAT) === false) {
            $errors['lat'] = 'lat must be a float';
        } else {
            $lat = (float) $latRaw;
            if ($lat < -90 || $lat > 90) {
                $errors['lat'] = 'lat must be between -90 and 90';
            } else {
                $normalized['lat'] = $lat;
            }
        }

        if ($lonRaw === null || $lonRaw === '') {
            $errors['lon'] = 'lon is required';
        } elseif (filter_var($lonRaw, FILTER_VALIDATE_FLOAT) === false) {
            $errors['lon'] = 'lon must be a float';
        } else {
            $lon = (float) $lonRaw;
            if ($lon < -180 || $lon > 180) {
                $errors['lon'] = 'lon must be between -180 and 180';
            } else {
                $normalized['lon'] = $lon;
            }
        }

        $units = $query['units'] ?? 'metric';
        if (!in_array($units, self::UNITS_ALLOWED, true)) {
            $errors['units'] = 'units must be metric, imperial, or standard';
        } else {
            $normalized['units'] = $units;
        }

        $lang = $query['lang'] ?? 'en';
        if (!is_string($lang) || $lang === '') {
            $errors['lang'] = 'lang must be a non-empty string';
        } else {
            $normalized['lang'] = $lang;
        }

        $exclude = $query['exclude'] ?? '';
        $excludeList = [];
        if ($exclude !== '') {
            $excludeList = array_values(array_filter(array_map('trim', explode(',', (string) $exclude)), 'strlen'));
            $excludeList = array_values(array_unique(array_map('strtolower', $excludeList)));
            foreach ($excludeList as $excludeValue) {
                if (!in_array($excludeValue, self::EXCLUDE_ALLOWED, true)) {
                    $errors['exclude'] = 'exclude has invalid values';
                    break;
                }
            }
        }
        sort($excludeList);
        $normalized['exclude'] = implode(',', $excludeList);

        $raw = $query['raw'] ?? '0';
        if (!in_array((string) $raw, ['0', '1'], true)) {
            $errors['raw'] = 'raw must be 0 or 1';
        } else {
            $normalized['raw'] = ((string) $raw) === '1';
        }

        return [$errors, $normalized];
    }

    private function json(ResponseInterface $response, int $status, array $payload): ResponseInterface
    {
        $response->getBody()->write((string) json_encode($payload));

        return $response
            ->withHeader('Content-Type', 'application/json')
            ->withStatus($status);
    }
}
