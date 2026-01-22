<?php

declare(strict_types=1);

namespace App\Service;

interface RateLimiterStore
{
    public function incr(string $key): int;

    public function expire(string $key, int $ttl): bool;

    public function ttl(string $key): int;
}
