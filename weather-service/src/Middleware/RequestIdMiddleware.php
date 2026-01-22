<?php

declare(strict_types=1);

namespace App\Middleware;

use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\ServerRequestInterface;
use Psr\Http\Server\MiddlewareInterface;
use Psr\Http\Server\RequestHandlerInterface;

final class RequestIdMiddleware implements MiddlewareInterface
{
    public function process(ServerRequestInterface $request, RequestHandlerInterface $handler): ResponseInterface
    {
        $requestId = $request->getHeaderLine('X-Request-Id');
        if ($requestId === '') {
            $requestId = $this->generateRequestId();
        }

        $_SERVER['HTTP_X_REQUEST_ID'] = $requestId;

        $request = $request->withAttribute('request_id', $requestId);
        $response = $handler->handle($request);

        return $response->withHeader('X-Request-Id', $requestId);
    }

    private function generateRequestId(): string
    {
        $hex = bin2hex(random_bytes(16));
        $parts = str_split($hex, 4);

        return sprintf(
            '%s%s-%s-%s-%s-%s%s%s',
            $parts[0],
            $parts[1],
            $parts[2],
            $parts[3],
            $parts[4],
            $parts[5],
            $parts[6],
            $parts[7]
        );
    }
}
