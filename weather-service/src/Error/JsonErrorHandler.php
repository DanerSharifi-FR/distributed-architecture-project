<?php

declare(strict_types=1);

namespace App\Error;

use App\Config;
use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\ServerRequestInterface;
use Slim\Psr7\Response;

final class JsonErrorHandler
{
    public function __invoke(
        ServerRequestInterface $request,
        \Throwable $exception,
        bool $displayErrorDetails,
        bool $logErrors,
        bool $logErrorDetails
    ): ResponseInterface {
        $requestId = (string) ($request->getAttribute('request_id')
            ?: $request->getHeaderLine('X-Request-Id')
            ?: ($_SERVER['HTTP_X_REQUEST_ID'] ?? ''));

        $payload = [
            'error_code' => 'INTERNAL_ERROR',
            'message' => 'Internal server error',
            'request_id' => $requestId,
        ];

        if ($this->shouldIncludeDebug()) {
            $payload['debug'] = [
                'type' => $exception::class,
                'message' => $exception->getMessage(),
                'trace' => $this->formatTrace($exception->getTrace(), 5),
            ];
        }

        $response = new Response(500);
        $response->getBody()->write((string) json_encode($payload));

        return $response->withHeader('Content-Type', 'application/json');
    }

    private function shouldIncludeDebug(): bool
    {
        if (Config::envBool('APP_DEBUG', false)) {
            return true;
        }

        return Config::envString('APP_ENV', '') === 'dev';
    }

    private function formatTrace(array $trace, int $limit): string
    {
        $frames = array_slice($trace, 0, $limit);
        $parts = [];

        foreach ($frames as $frame) {
            $file = $frame['file'] ?? 'unknown';
            $line = $frame['line'] ?? 0;
            $function = $frame['function'] ?? 'unknown';
            $parts[] = sprintf('%s:%s %s()', $file, $line, $function);
        }

        return implode(' | ', $parts);
    }
}
