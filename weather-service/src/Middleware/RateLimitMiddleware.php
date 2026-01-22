<?php

declare(strict_types=1);

namespace App\Middleware;

use App\Service\RateLimiter;
use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\ServerRequestInterface;
use Psr\Http\Server\MiddlewareInterface;
use Psr\Http\Server\RequestHandlerInterface;
use Slim\Psr7\Response;

final class RateLimitMiddleware implements MiddlewareInterface
{
    public function __construct(private readonly RateLimiter $rateLimiter)
    {
    }

    public function process(ServerRequestInterface $request, RequestHandlerInterface $handler): ResponseInterface
    {
        $callerId = $this->resolveCallerId($request);
        $result = $this->rateLimiter->check($callerId);

        if (!$result['allowed']) {
            $retryAfter = $result['retry_after_s'];
            $payload = [
                'error_code' => 'RATE_LIMITED',
                'message' => 'Too many requests',
                'request_id' => (string) $request->getAttribute('request_id'),
                'retry_after_s' => $retryAfter,
            ];

            $response = new Response(429);
            $response->getBody()->write((string) json_encode($payload));

            return $response
                ->withHeader('Content-Type', 'application/json')
                ->withHeader('Retry-After', (string) $retryAfter);
        }

        return $handler->handle($request);
    }

    private function resolveCallerId(ServerRequestInterface $request): string
    {
        $caller = $request->getHeaderLine('X-Caller-Id');
        if ($caller !== '') {
            return $caller;
        }

        $server = $request->getServerParams();
        $ip = $server['REMOTE_ADDR'] ?? 'unknown';

        return (string) $ip;
    }
}
