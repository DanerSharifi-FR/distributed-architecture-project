<?php

declare(strict_types=1);

namespace Tests\Service;

use App\Service\RateLimiter;
use App\Service\RateLimiterStore;
use PHPUnit\Framework\TestCase;

final class RateLimiterTest extends TestCase
{
    public function testRateLimiterBlocksAfterLimit(): void
    {
        $counts = [];
        $ttls = [];

        $store = new class($counts, $ttls) implements RateLimiterStore {
            public function __construct(private array &$counts, private array &$ttls)
            {
            }

            public function incr(string $key): int
            {
                $this->counts[$key] = ($this->counts[$key] ?? 0) + 1;
                if ($this->counts[$key] === 1) {
                    $this->ttls[$key] = 60;
                }

                return $this->counts[$key];
            }

            public function expire(string $key, int $ttl): bool
            {
                $this->ttls[$key] = $ttl;
                return true;
            }

            public function ttl(string $key): int
            {
                return $this->ttls[$key] ?? 0;
            }
        };

        $limiter = new RateLimiter($store, 2, 1);

        $first = $limiter->check('caller-1');
        $second = $limiter->check('caller-1');

        self::assertTrue($first['allowed']);
        self::assertFalse($second['allowed']);
        self::assertSame(60, $second['retry_after_s']);
    }
}
