<?php

declare(strict_types=1);

namespace App\Service;

final class RateLimiter
{
    public function __construct(
        private readonly RateLimiterStore $store,
        private readonly int $globalPerMinute,
        private readonly int $callerPerMinute
    ) {
    }

    /**
     * @return array{allowed: bool, retry_after_s: int}
     */
    public function check(string $callerId): array
    {
        $window = (int) floor(time() / 60);
        $keys = [
            'global' => sprintf('rate:global:%d', $window),
            'caller' => sprintf('rate:caller:%s:%d', $callerId, $window),
        ];

        $retryAfter = 0;
        $allowed = true;

        try {
            $globalCount = $this->increment($keys['global']);
            $callerCount = $this->increment($keys['caller']);

            if ($this->globalPerMinute > 0 && $globalCount > $this->globalPerMinute) {
                $allowed = false;
                $retryAfter = max($retryAfter, $this->ttl($keys['global']));
            }

            if ($this->callerPerMinute > 0 && $callerCount > $this->callerPerMinute) {
                $allowed = false;
                $retryAfter = max($retryAfter, $this->ttl($keys['caller']));
            }
        } catch (\Throwable) {
            return ['allowed' => true, 'retry_after_s' => 0];
        }

        return [
            'allowed' => $allowed,
            'retry_after_s' => $allowed ? 0 : max(1, $retryAfter),
        ];
    }

    private function increment(string $key): int
    {
        $count = $this->store->incr($key);
        if ($count === 1) {
            $this->store->expire($key, 60);
        }

        return (int) $count;
    }

    private function ttl(string $key): int
    {
        $ttl = $this->store->ttl($key);
        if ($ttl < 0) {
            return 0;
        }

        return (int) $ttl;
    }
}
