<?php

declare(strict_types=1);

namespace Tests\Controller;

use App\Controller\WeatherController;
use App\Service\OpenWeatherClient;
use App\Service\WeatherCache;
use App\Service\WeatherNormalizer;
use PHPUnit\Framework\TestCase;
use Psr\Log\LoggerInterface;
use Slim\Psr7\Factory\ServerRequestFactory;
use Slim\Psr7\Response;

final class WeatherControllerTest extends TestCase
{
    public function testMissingLatLonReturnsValidationError(): void
    {
        $cache = $this->createMock(WeatherCache::class);
        $client = $this->createMock(OpenWeatherClient::class);
        $normalizer = new WeatherNormalizer();
        $logger = $this->createMock(LoggerInterface::class);

        $controller = new WeatherController($cache, $client, $normalizer, $logger);

        $request = (new ServerRequestFactory())->createServerRequest('GET', '/v1/onecall');
        $request = $request->withAttribute('request_id', 'test-request');
        $response = new Response();

        $result = $controller->onecall($request, $response);

        self::assertSame(400, $result->getStatusCode());
        $payload = json_decode((string) $result->getBody(), true);

        self::assertSame('VALIDATION_ERROR', $payload['error_code']);
        self::assertArrayHasKey('lat', $payload['details']);
        self::assertArrayHasKey('lon', $payload['details']);
    }

    public function testUpstreamAuthErrorMapsToCustomCode(): void
    {
        $cache = $this->createMock(WeatherCache::class);
        $cache->method('getBucketDegrees')->willReturn(0.05);
        $cache->method('get')->willReturn(null);

        $client = $this->createMock(OpenWeatherClient::class);
        $client->method('buildOneCallSanitizedUrl')->willReturn('https://api.openweathermap.org/data/3.0/onecall?appid=***');
        $client->method('buildOneCallSanitizedUrl')->willReturn('https://api.openweathermap.org/data/3.0/onecall?appid=***');
        $client->method('fetchOneCall')->willReturn([
            'ok' => false,
            'status' => 401,
            'error_message' => 'Invalid API key',
            'body_snippet' => '{"cod":401,"message":"Invalid API key"}',
            'upstream_ms' => 42,
        ]);

        $normalizer = new WeatherNormalizer();
        $logger = $this->createMock(LoggerInterface::class);

        $controller = new WeatherController($cache, $client, $normalizer, $logger);

        $request = (new ServerRequestFactory())->createServerRequest('GET', '/v1/onecall');
        $request = $request->withAttribute('request_id', 'test-request');
        $request = $request->withQueryParams(['lat' => '10.0', 'lon' => '20.0']);
        $response = new Response();

        $result = $controller->onecall($request, $response);

        self::assertSame(502, $result->getStatusCode());
        $payload = json_decode((string) $result->getBody(), true);
        self::assertSame('UPSTREAM_AUTH_ERROR', $payload['error_code']);
    }

    public function testUpstreamErrorIncludesDebugInDev(): void
    {
        putenv('APP_ENV=dev');

        try {
            $cache = $this->createMock(WeatherCache::class);
            $cache->method('getBucketDegrees')->willReturn(0.05);
            $cache->method('get')->willReturn(null);

            $client = $this->createMock(OpenWeatherClient::class);
            $client->method('buildOneCallSanitizedUrl')->willReturn('https://api.openweathermap.org/data/3.0/onecall?appid=***');
            $client->method('fetchOneCall')->willReturn([
                'ok' => false,
                'status' => 500,
                'error_message' => 'Upstream exploded',
                'body_snippet' => 'failure',
                'upstream_ms' => 12,
            ]);

            $normalizer = new WeatherNormalizer();
            $logger = $this->createMock(LoggerInterface::class);

            $controller = new WeatherController($cache, $client, $normalizer, $logger);

            $request = (new ServerRequestFactory())->createServerRequest('GET', '/v1/onecall');
            $request = $request->withAttribute('request_id', 'test-request');
            $request = $request->withQueryParams(['lat' => '10.0', 'lon' => '20.0']);
            $response = new Response();

            $result = $controller->onecall($request, $response);

            self::assertSame(502, $result->getStatusCode());
            $payload = json_decode((string) $result->getBody(), true);
            self::assertSame('UPSTREAM_ERROR', $payload['error_code']);
            self::assertArrayHasKey('debug', $payload);
        } finally {
            putenv('APP_ENV');
        }
    }
}
