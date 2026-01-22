<?php

declare(strict_types=1);

namespace Tests\Service;

use App\Service\OpenWeatherClient;
use PHPUnit\Framework\TestCase;
use Symfony\Contracts\HttpClient\HttpClientInterface;

final class OpenWeatherClientTest extends TestCase
{
    public function testBuildOneCallUrlIncludesPathAndQuery(): void
    {
        $client = $this->createMock(HttpClientInterface::class);
        $openWeather = new OpenWeatherClient(
            $client,
            'https://api.openweathermap.org',
            'test-key',
            1000,
            3000,
            0
        );

        $url = $openWeather->buildOneCallUrl(43.6, 1.44, 'metric', 'en', '');
        $parts = parse_url($url);

        self::assertSame('/data/3.0/onecall', $parts['path'] ?? null);
        $query = [];
        parse_str($parts['query'] ?? '', $query);

        self::assertSame('43.6', $query['lat'] ?? null);
        self::assertSame('1.44', $query['lon'] ?? null);
        self::assertSame('test-key', $query['appid'] ?? null);
    }
}
