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
use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\ServerRequestInterface;
use Slim\Factory\AppFactory;
use Slim\Psr7\Response;

final class App
{
    public static function create(ContainerInterface $container): \Slim\App
    {
        AppFactory::setContainer($container);
        $app = AppFactory::create();

        $app->get('/healthz', [HealthController::class, 'healthz']);
        $app->get('/readyz', [HealthController::class, 'readyz']);
        $app->get('/openapi.yaml', function (ServerRequestInterface $request, ResponseInterface $response): ResponseInterface {
            $path = dirname(__DIR__) . '/docs/openapi.yaml';
            $contents = is_file($path) ? (string) file_get_contents($path) : '';

            if ($contents === '') {
                return $response->withStatus(404);
            }

            $response->getBody()->write($contents);

            return $response->withHeader('Content-Type', 'application/yaml');
        });
        $app->get('/docs', function (ServerRequestInterface $request, ResponseInterface $response): ResponseInterface {
            $html = '<!doctype html>'
                . '<html lang="en"><head>'
                . '<meta charset="utf-8"/>'
                . '<meta name="viewport" content="width=device-width, initial-scale=1"/>'
                . '<title>Weather Service API Docs</title>'
                . '<link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css"/>'
                . '</head><body>'
                . '<div id="swagger-ui"></div>'
                . '<script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"></script>'
                . '<script>window.ui = SwaggerUIBundle({url: "/openapi.yaml", dom_id: "#swagger-ui"});</script>'
                . '</body></html>';

            $response = $response instanceof Response ? $response : new Response();
            $response->getBody()->write($html);

            return $response->withHeader('Content-Type', 'text/html; charset=utf-8');
        });

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
