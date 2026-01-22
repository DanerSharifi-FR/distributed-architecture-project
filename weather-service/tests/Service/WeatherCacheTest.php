<?php

declare(strict_types=1);

namespace Tests\Service;

use App\Service\WeatherCache;
use PHPUnit\Framework\TestCase;

final class WeatherCacheTest extends TestCase
{
    public function testBucketCoordinateRoundsToBucket(): void
    {
        $bucketDegrees = 0.05;

        self::assertSame(48.85, WeatherCache::bucketCoordinate(48.8566, $bucketDegrees));
        self::assertSame(-122.4, WeatherCache::bucketCoordinate(-122.4194, $bucketDegrees));
    }

    public function testBuildKeyIncludesBucketedCoordinatesAndParams(): void
    {
        $key = WeatherCache::buildKey(48.8566, 2.3522, 'metric', 'en', 'alerts', 0.05);

        self::assertSame(
            'weather:v1:lat=48.85000:lon=2.35000:units=metric:lang=en:exclude=alerts',
            $key
        );
    }
}
