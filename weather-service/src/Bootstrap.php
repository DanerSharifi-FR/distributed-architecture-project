<?php

declare(strict_types=1);

namespace App;

use App\Service\OpenWeatherClient;
use App\Service\RateLimiter;
use App\Service\RateLimiterStore;
use App\Service\RedisRateLimiterStore;
use App\Service\WeatherCache;
use App\Service\WeatherNormalizer;
use DI\ContainerBuilder;
use Monolog\Formatter\JsonFormatter;
use Monolog\Handler\StreamHandler;
use Monolog\Logger;
use Monolog\LogRecord;
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
                $logger->pushProcessor(static function (LogRecord $record): LogRecord {
                    $requestId = $record->context['request_id'] ?? $record->extra['request_id'] ?? null;
                    if ($requestId === null || $requestId === '') {
                        $requestId = $_SERVER['HTTP_X_REQUEST_ID'] ?? null;
                    }

                    if ($requestId === null || $requestId === '') {
                        return $record;
                    }

                    return $record->with(extra: $record->extra + ['request_id' => $requestId]);
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
            RateLimiterStore::class => function (\Redis $redis): RateLimiterStore {
                return new RedisRateLimiterStore($redis);
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
            RateLimiter::class => function (RateLimiterStore $store): RateLimiter {
                $global = Config::envInt('RATE_LIMIT_GLOBAL_PER_MIN', 300) ?? 300;
                $caller = Config::envInt('RATE_LIMIT_CALLER_PER_MIN', 60) ?? 60;

                return new RateLimiter($store, $global, $caller);
            },
        ]);

        $container = $containerBuilder->build();
        self::validateProdConfig($container->get(LoggerInterface::class));

        return App::create($container);
    }

    private static function validateProdConfig(LoggerInterface $logger): void
    {
        if (Config::envString('APP_ENV', '') !== 'prod') {
            return;
        }

        $token = Config::envString('INTERNAL_TOKEN', '') ?? '';
        if ($token === '') {
            $logger->error('INTERNAL_TOKEN must be set when APP_ENV=prod');
        }
    }
}
