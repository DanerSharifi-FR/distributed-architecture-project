<?php

declare(strict_types=1);

namespace App;

use App\Service\OpenWeatherClient;
use App\Service\WeatherCache;
use App\Service\WeatherNormalizer;
use DI\ContainerBuilder;
use Monolog\Formatter\JsonFormatter;
use Monolog\Handler\StreamHandler;
use Monolog\Logger;
use Psr\Log\LoggerInterface;
use Symfony\Component\HttpClient\HttpClient;
use Symfony\Contracts\HttpClient\HttpClientInterface;

final class Bootstrap
{
    public static function createApp(): \Slim\App
    {
        $containerBuilder = new ContainerBuilder();

        $containerBuilder->addDefinitions([
            LoggerInterface::class => function (): LoggerInterface {
                $logger = new Logger('app');
                $handler = new StreamHandler('php://stdout');
                $handler->setFormatter(new JsonFormatter());
                $logger->pushHandler($handler);
                $logger->pushProcessor(static function (array $record): array {
                    if (!isset($record['context']['request_id']) && isset($_SERVER['HTTP_X_REQUEST_ID'])) {
                        $record['context']['request_id'] = $_SERVER['HTTP_X_REQUEST_ID'];
                    }

                    return $record;
                });

                return $logger;
            },
            'logger' => \DI\get(LoggerInterface::class),
            HttpClientInterface::class => function (): HttpClientInterface {
                return HttpClient::create();
            },
            \Redis::class => function (): \Redis {
                $redisUrl = Config::envString('REDIS_URL', '');
                if ($redisUrl === null || $redisUrl === '') {
                    throw new \RuntimeException('REDIS_URL not configured');
                }

                if (!class_exists(\Redis::class)) {
                    throw new \RuntimeException('redis extension not installed');
                }

                $parts = parse_url($redisUrl);
                if ($parts === false || !isset($parts['host'])) {
                    throw new \RuntimeException('Invalid REDIS_URL');
                }

                $host = $parts['host'];
                $port = (int) ($parts['port'] ?? 6379);
                $timeout = 0.5;

                $redis = new \Redis();
                if ($redis->connect($host, $port, $timeout) === false) {
                    throw new \RuntimeException('Unable to connect to Redis');
                }

                if (isset($parts['pass'])) {
                    $auth = $parts['pass'];
                    if (isset($parts['user'])) {
                        $auth = [$parts['user'], $parts['pass']];
                    }

                    if ($redis->auth($auth) === false) {
                        throw new \RuntimeException('Redis authentication failed');
                    }
                }

                return $redis;
            },
            WeatherCache::class => function (\Redis $redis): WeatherCache {
                $ttl = Config::envInt('CACHE_TTL_SECONDS', 600) ?? 600;
                $maxStale = Config::envInt('CACHE_MAX_STALE_SECONDS', 1800) ?? 1800;
                $bucket = Config::envFloat('WEATHER_CACHE_BUCKET_DEG', 0.05) ?? 0.05;

                return new WeatherCache($redis, $ttl, $maxStale, $bucket);
            },
            WeatherNormalizer::class => \DI\autowire(),
            OpenWeatherClient::class => function (HttpClientInterface $client): OpenWeatherClient {
                $baseUrl = Config::envString('OPENWEATHER_BASE_URL', 'https://api.openweathermap.org') ?? '';
                $apiKey = Config::envString('OPENWEATHER_API_KEY', '') ?? '';
                $connectTimeoutMs = Config::envInt('OPENWEATHER_CONNECT_TIMEOUT_MS', 1000) ?? 1000;
                $timeoutMs = Config::envInt('OPENWEATHER_TIMEOUT_MS', 3000) ?? 3000;
                $retries = Config::envInt('OPENWEATHER_RETRIES', 2) ?? 2;

                return new OpenWeatherClient(
                    $client,
                    $baseUrl,
                    $apiKey,
                    $connectTimeoutMs,
                    $timeoutMs,
                    $retries
                );
            },
        ]);

        $container = $containerBuilder->build();

        return App::create($container);
    }
}
