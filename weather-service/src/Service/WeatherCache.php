<?php

declare(strict_types=1);

namespace App\Service;

class WeatherCache
{
    private int $ttlSeconds;
    private int $maxStaleSeconds;
    private float $bucketDegrees;

    public function __construct(
        private readonly \Redis $redis,
        int $ttlSeconds,
        int $maxStaleSeconds,
        float $bucketDegrees
    ) {
        $this->ttlSeconds = max(0, $ttlSeconds);
        $this->maxStaleSeconds = max(0, $maxStaleSeconds);
        $this->bucketDegrees = $bucketDegrees > 0 ? $bucketDegrees : 0.05;
    }

    public function get(string $key): ?array
    {
        $value = $this->redis->get($key);
        if ($value === false || $value === null) {
            return null;
        }

        $decoded = json_decode((string) $value, true);
        if (!is_array($decoded) || !isset($decoded['cached_at'], $decoded['payload'])) {
            return null;
        }

        return $decoded;
    }

    public function set(string $key, array $payload): void
    {
        $cachedAt = time();
        $data = [
            'cached_at' => $cachedAt,
            'payload' => $payload,
        ];

        $ttl = max($this->ttlSeconds, $this->maxStaleSeconds);
        $this->redis->setex($key, $ttl, (string) json_encode($data));
    }

    public function isFresh(int $cachedAt): bool
    {
        return $this->ageSeconds($cachedAt) <= $this->ttlSeconds;
    }

    public function isWithinMaxStale(int $cachedAt): bool
    {
        return $this->ageSeconds($cachedAt) <= $this->maxStaleSeconds;
    }

    public function ageSeconds(int $cachedAt): int
    {
        return max(0, time() - $cachedAt);
    }

    public function getBucketDegrees(): float
    {
        return $this->bucketDegrees;
    }

    public static function bucketCoordinate(float $value, float $bucketDegrees): float
    {
        if ($bucketDegrees <= 0) {
            return $value;
        }

        $bucketed = round($value / $bucketDegrees) * $bucketDegrees;
        if (abs($bucketed) < 0.0000001) {
            $bucketed = 0.0;
        }

        return $bucketed;
    }

    public static function buildKey(
        float $lat,
        float $lon,
        string $units,
        string $lang,
        string $exclude,
        float $bucketDegrees
    ): string {
        $bucketLat = self::bucketCoordinate($lat, $bucketDegrees);
        $bucketLon = self::bucketCoordinate($lon, $bucketDegrees);

        $latKey = sprintf('%.5f', $bucketLat);
        $lonKey = sprintf('%.5f', $bucketLon);

        return sprintf(
            'weather:v1:lat=%s:lon=%s:units=%s:lang=%s:exclude=%s',
            $latKey,
            $lonKey,
            $units,
            $lang,
            $exclude
        );
    }
}
