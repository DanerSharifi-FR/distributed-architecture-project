<?php

declare(strict_types=1);

namespace Tests\Controller;

use App\Controller\HealthController;
use PHPUnit\Framework\TestCase;
use Psr\Log\LoggerInterface;
use Slim\Psr7\Factory\ResponseFactory;
use Slim\Psr7\Factory\ServerRequestFactory;

final class HealthControllerTest extends TestCase
{
    public function testReadyzFailsWhenProdMissingInternalToken(): void
    {
        putenv('APP_ENV=prod');
        putenv('INTERNAL_TOKEN=');

        try {
            $logger = $this->createMock(LoggerInterface::class);
            $controller = new HealthController($logger);

            $request = (new ServerRequestFactory())->createServerRequest('GET', '/readyz');
            $response = (new ResponseFactory())->createResponse();

            $result = $controller->readyz($request, $response);

            self::assertSame(503, $result->getStatusCode());
            $payload = json_decode((string) $result->getBody(), true);
            self::assertSame('INTERNAL_TOKEN not set for prod', $payload['message']);
        } finally {
            putenv('APP_ENV');
            putenv('INTERNAL_TOKEN');
        }
    }
}
