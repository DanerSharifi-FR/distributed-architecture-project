<?php

declare(strict_types=1);

namespace Tests\Service;

use App\Service\WeatherNormalizer;
use PHPUnit\Framework\TestCase;

final class WeatherNormalizerTest extends TestCase
{
    public function testNormalizeProducesDeterministicKeys(): void
    {
        $payload = [
            'current' => [
                'dt' => 123,
                'temp' => 18.5,
                'weather' => [
                    [
                        'id' => 800,
                        'main' => 'Clear',
                        'description' => 'clear sky',
                        'icon' => '01d',
                    ],
                ],
            ],
            'hourly' => [
                [
                    'dt' => 124,
                    'temp' => 18.0,
                ],
            ],
        ];

        $normalizer = new WeatherNormalizer();
        $normalized = $normalizer->normalize($payload, true);

        self::assertSame(123, $normalized['current']['dt']);
        self::assertNull($normalized['current']['humidity']);
        self::assertSame(124, $normalized['hourly'][0]['dt']);
        self::assertNull($normalized['hourly'][0]['humidity']);
        self::assertSame($payload, $normalized['raw']);

        $normalized = $normalizer->applyRawPreference($normalized, false);
        self::assertNull($normalized['raw']);
    }
}
