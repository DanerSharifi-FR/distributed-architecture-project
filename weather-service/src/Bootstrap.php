<?php

declare(strict_types=1);

namespace App;

use DI\ContainerBuilder;
use Monolog\Formatter\JsonFormatter;
use Monolog\Handler\StreamHandler;
use Monolog\Logger;
use Psr\Log\LoggerInterface;

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
        ]);

        $container = $containerBuilder->build();

        return App::create($container);
    }
}
