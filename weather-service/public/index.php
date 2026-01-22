<?php

declare(strict_types=1);

require __DIR__ . '/../vendor/autoload.php';

use App\Bootstrap;
use Dotenv\Dotenv;

$dotenvPath = dirname(__DIR__);
if (is_file($dotenvPath . '/.env')) {
    Dotenv::createImmutable($dotenvPath)->safeLoad();
}

$app = Bootstrap::createApp();
$app->run();
