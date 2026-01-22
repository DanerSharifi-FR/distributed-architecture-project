<?php

declare(strict_types=1);

namespace App\Service;

final class RedisRateLimiterStore implements RateLimiterStore
{
    public function __construct(private readonly \Redis $redis)
    {
    }

    public function incr(string $key): int
    {
        return (int) $this->redis->incr($key);
    }

    public function expire(string $key, int $ttl): bool
    {
        return (bool) $this->redis->expire($key, $ttl);
    }

    public function ttl(string $key): int
    {
        return (int) $this->redis->ttl($key);
    }
}
