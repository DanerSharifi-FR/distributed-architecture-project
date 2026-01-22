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
}
