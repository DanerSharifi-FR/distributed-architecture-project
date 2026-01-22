<?php

declare(strict_types=1);

namespace App;

use App\Controller\HealthController;
use App\Controller\WeatherController;
use App\Middleware/InternalAuthMiddleware;
use App\Middleware\RequestIdMiddleware;
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
            $group->get('/onecall', [WeatherController::class, 'onecall']);
        })->add(InternalAuthMiddleware::class);

        $app->addRoutingMiddleware();
        $app->addErrorMiddleware(true, false, false);
        $app->add(RequestIdMiddleware::class);

        return $app;
    }
}
