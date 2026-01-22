<?php

declare(strict_types=1);

namespace App\Controller;

use App\Config;
use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\ServerRequestInterface;
use Psr\Log\LoggerInterface;

final class HealthController
{
    public function __construct(private readonly LoggerInterface $logger)
    {
    }

    public function healthz(ServerRequestInterface $request, ResponseInterface $response): ResponseInterface
    {
        return $this->json($response, 200, ['status' => 'ok']);
    }

    public function readyz(ServerRequestInterface $request, ResponseInterface $response): ResponseInterface
    {
        $redisUrl = Config::envString('REDIS_URL');
        if ($redisUrl === null || $redisUrl === '') {
            return $this->json($response, 503, [
                'status' => 'error',
                'message' => 'REDIS_URL not set',
            ]);
        }

        if (!class_exists(\Redis::class)) {
            return $this->json($response, 503, [
                'status' => 'error',
                'message' => 'redis extension not installed',
            ]);
        }

        $parts = parse_url($redisUrl);
        if ($parts === false || !isset($parts['host'])) {
            return $this->json($response, 503, [
                'status' => 'error',
                'message' => 'invalid REDIS_URL',
            ]);
        }

        $host = $parts['host'];
        $port = $parts['port'] ?? 6379;
        $timeout = 0.5;

        try {
            $redis = new \Redis();
            if ($redis->connect($host, (int) $port, $timeout) === false) {
                return $this->json($response, 503, [
                    'status' => 'error',
                    'message' => 'unable to connect to redis',
                ]);
            }

            if (isset($parts['pass'])) {
                $auth = $parts['pass'];
                if (isset($parts['user'])) {
                    $auth = [$parts['user'], $parts['pass']];
                }

                if ($redis->auth($auth) === false) {
                    return $this->json($response, 503, [
                        'status' => 'error',
                        'message' => 'redis auth failed',
                    ]);
                }
            }

            $pong = $redis->ping();
            if ($pong !== '+PONG' && $pong !== 'PONG' && $pong !== true) {
                return $this->json($response, 503, [
                    'status' => 'error',
                    'message' => 'redis ping failed',
                ]);
            }
        } catch (\Throwable $e) {
            $this->logger->warning('Redis readyz failed', [
                'error' => $e->getMessage(),
                'request_id' => $request->getAttribute('request_id'),
            ]);

            return $this->json($response, 503, [
                'status' => 'error',
                'message' => 'redis error',
            ]);
        }

        return $this->json($response, 200, ['status' => 'ok']);
    }

    private function json(ResponseInterface $response, int $status, array $payload): ResponseInterface
    {
        $response->getBody()->write((string) json_encode($payload));

        return $response
            ->withHeader('Content-Type', 'application/json')
            ->withStatus($status);
    }
}
