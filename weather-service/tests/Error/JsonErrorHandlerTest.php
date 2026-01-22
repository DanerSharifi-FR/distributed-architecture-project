<?php

declare(strict_types=1);

namespace Tests\Error;

use App\Error\JsonErrorHandler;
use PHPUnit\Framework\TestCase;
use Slim\Psr7\Factory\ServerRequestFactory;

final class JsonErrorHandlerTest extends TestCase
{
    public function testDevErrorIncludesDebug(): void
    {
        putenv('APP_ENV=dev');

        try {
            $handler = new JsonErrorHandler();
            $request = (new ServerRequestFactory())->createServerRequest('GET', '/boom')
                ->withAttribute('request_id', 'test-id');

            $response = $handler($request, new \RuntimeException('boom'), true, false, false);
            $payload = json_decode((string) $response->getBody(), true);

            self::assertSame(500, $response->getStatusCode());
            self::assertSame('INTERNAL_ERROR', $payload['error_code']);
            self::assertSame('test-id', $payload['request_id']);
            self::assertArrayHasKey('debug', $payload);
            self::assertSame(\RuntimeException::class, $payload['debug']['type']);
        } finally {
            putenv('APP_ENV');
        }
    }

    public function testProdErrorOmitsDebug(): void
    {
        putenv('APP_ENV=prod');

        try {
            $handler = new JsonErrorHandler();
            $request = (new ServerRequestFactory())->createServerRequest('GET', '/boom')
                ->withAttribute('request_id', 'test-id');

            $response = $handler($request, new \RuntimeException('boom'), true, false, false);
            $payload = json_decode((string) $response->getBody(), true);

            self::assertSame(500, $response->getStatusCode());
            self::assertSame('INTERNAL_ERROR', $payload['error_code']);
            self::assertSame('test-id', $payload['request_id']);
            self::assertArrayNotHasKey('debug', $payload);
        } finally {
            putenv('APP_ENV');
        }
    }
}
