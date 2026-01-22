<?php

declare(strict_types=1);

namespace App;

use App\Config;
use App\Controller\HealthController;
use App\Controller\WeatherController;
use App\Error\JsonErrorHandler;
use App\Middleware\InternalAuthMiddleware;
use App\Middleware\RequestIdMiddleware;
use App\Middleware\RateLimitMiddleware;
use Psr\Container\ContainerInterface;
use Slim\Factory\AppFactory;

final class App
{
    public static function create(ContainerInterface $container): \Slim\App
    {
        AppFactory::setContainer($container);
        $app = AppFactory::create();

        $app->get('/healthz', [HealthController::class, 'healthz']);
        $app->get('/readyz', [HealthController::class, 'readyz']);

        $app->group('/v1', function ($group): void {
            $route = $group->get('/onecall', [WeatherController::class, 'onecall']);
            $route->add(RateLimitMiddleware::class);
        })->add(InternalAuthMiddleware::class);

        if (Config::envBool('APP_DEBUG', false) || Config::envString('APP_ENV', '') === 'dev') {
            $app->get('/debug/upstream/onecall', [WeatherController::class, 'debugOnecall']);
        }

        $app->addRoutingMiddleware();
        $errorMiddleware = $app->addErrorMiddleware(true, false, false);
        $errorMiddleware->setDefaultErrorHandler(JsonErrorHandler::class);
        $app->add(RequestIdMiddleware::class);

        return $app;
    }
}
