<?php

declare(strict_types=1);

namespace App;

final class Config
{
    private static function readEnv(string $key): ?string
    {
        $value = getenv($key);
        if ($value !== false) {
            return (string) $value;
        }

        if (isset($_ENV[$key])) {
            return (string) $_ENV[$key];
        }

        return null;
    }

    public static function envString(string $key, ?string $default = null): ?string
    {
        $value = self::readEnv($key);
        if ($value === null) {
            return $default;
        }

        return $value;
    }

    public static function envInt(string $key, ?int $default = null): ?int
    {
        $value = self::readEnv($key);
        if ($value === null || $value === '') {
            return $default;
        }

        if (filter_var($value, FILTER_VALIDATE_INT) === false) {
            return $default;
        }

        return (int) $value;
    }

    public static function envFloat(string $key, ?float $default = null): ?float
    {
        $value = self::readEnv($key);
        if ($value === null || $value === '') {
            return $default;
        }

        if (filter_var($value, FILTER_VALIDATE_FLOAT) === false) {
            return $default;
        }

        return (float) $value;
    }

    public static function envBool(string $key, bool $default = false): bool
    {
        $value = self::readEnv($key);
        if ($value === null || $value === '') {
            return $default;
        }

        $normalized = strtolower((string) $value);
        $truthy = ['1', 'true', 'yes', 'on'];
        $falsy = ['0', 'false', 'no', 'off'];

        if (in_array($normalized, $truthy, true)) {
            return true;
        }

        if (in_array($normalized, $falsy, true)) {
            return false;
        }

        return $default;
    }
}
