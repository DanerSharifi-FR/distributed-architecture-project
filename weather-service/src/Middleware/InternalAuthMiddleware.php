<?php

declare(strict_types=1);

namespace App\Middleware;

use App\Config;
use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\ServerRequestInterface;
use Psr\Http\Server\MiddlewareInterface;
use Psr\Http\Server\RequestHandlerInterface;
use Slim\Psr7\Response;

final class InternalAuthMiddleware implements MiddlewareInterface
{
    public function process(ServerRequestInterface $request, RequestHandlerInterface $handler): ResponseInterface
    {
        $expectedToken = Config::envString('INTERNAL_TOKEN', '') ?? '';
        if ($expectedToken === '') {
            return $handler->handle($request);
        }

        $providedToken = $request->getHeaderLine('X-Internal-Token');
        if (!hash_equals($expectedToken, $providedToken)) {
            return $this->unauthorizedResponse($request);
        }

        return $handler->handle($request);
    }

    private function unauthorizedResponse(ServerRequestInterface $request): ResponseInterface
    {
        $payload = [
            'error_code' => 'UNAUTHORIZED',
            'message' => 'Invalid internal token',
            'request_id' => (string) $request->getAttribute('request_id'),
        ];

        $response = new Response(401);
        $response->getBody()->write((string) json_encode($payload));

        return $response->withHeader('Content-Type', 'application/json');
    }
}
