<?php

declare(strict_types=1);

namespace App;

use App\Controller\HealthController;
use App\Middleware\RequestIdMiddleware;
use Psr\Container\ContainerInterface;
use Slim\Factory\AppFactory;

final class App
{
    public static function create(ContainerInterface $container): \Slim\App
    {
        AppFactory::setContainer($container);
        $app = AppFactory::create();

        $app->add(RequestIdMiddleware::class);

        $app->get('/healthz', [HealthController::class, 'healthz']);
        $app->get('/readyz', [HealthController::class, 'readyz']);

        $app->addRoutingMiddleware();
        $app->addErrorMiddleware(true, false, false);

        return $app;
    }
}
