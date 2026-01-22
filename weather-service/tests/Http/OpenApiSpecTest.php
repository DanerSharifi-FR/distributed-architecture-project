<?php

declare(strict_types=1);

namespace Tests\Http;

use App\App;
use DI\ContainerBuilder;
use PHPUnit\Framework\TestCase;
use Slim\Psr7\Factory\ServerRequestFactory;

final class OpenApiSpecTest extends TestCase
{
    public function testOpenApiSpecIsServed(): void
    {
        $container = (new ContainerBuilder())->build();
        $app = App::create($container);

        $request = (new ServerRequestFactory())->createServerRequest('GET', '/openapi.yaml');
        $response = $app->handle($request);

        self::assertSame(200, $response->getStatusCode());
        self::assertStringContainsString('openapi: 3.0.3', (string) $response->getBody());
    }
}
