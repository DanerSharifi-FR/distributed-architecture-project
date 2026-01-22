<?php

declare(strict_types=1);

namespace App\Service;

final class WeatherNormalizer
{
    public function normalize(array $payload, bool $includeRaw): array
    {
        $current = is_array($payload['current'] ?? null) ? $payload['current'] : [];
        $hourly = is_array($payload['hourly'] ?? null) ? $payload['hourly'] : [];
        $alerts = is_array($payload['alerts'] ?? null) ? $payload['alerts'] : [];

        return [
            'current' => $this->normalizeCurrent($current),
            'hourly' => $this->normalizeHourly($hourly),
            'alerts' => $this->normalizeAlerts($alerts),
            'raw' => $includeRaw ? $payload : null,
        ];
    }

    public function applyRawPreference(array $normalized, bool $includeRaw): array
    {
        if (!$includeRaw) {
            $normalized['raw'] = null;
        }

        return $normalized;
    }

    private function normalizeCurrent(array $current): array
    {
        return [
            'dt' => $this->valueOrNull($current, 'dt'),
            'sunrise' => $this->valueOrNull($current, 'sunrise'),
            'sunset' => $this->valueOrNull($current, 'sunset'),
            'temp' => $this->valueOrNull($current, 'temp'),
            'feels_like' => $this->valueOrNull($current, 'feels_like'),
            'pressure' => $this->valueOrNull($current, 'pressure'),
            'humidity' => $this->valueOrNull($current, 'humidity'),
            'dew_point' => $this->valueOrNull($current, 'dew_point'),
            'uvi' => $this->valueOrNull($current, 'uvi'),
            'clouds' => $this->valueOrNull($current, 'clouds'),
            'visibility' => $this->valueOrNull($current, 'visibility'),
            'wind_speed' => $this->valueOrNull($current, 'wind_speed'),
            'wind_deg' => $this->valueOrNull($current, 'wind_deg'),
            'wind_gust' => $this->valueOrNull($current, 'wind_gust'),
            'weather' => $this->normalizeWeather($current['weather'] ?? null),
        ];
    }

    private function normalizeHourly(array $hourly): array
    {
        $normalized = [];

        foreach ($hourly as $entry) {
            if (!is_array($entry)) {
                continue;
            }

            $normalized[] = [
                'dt' => $this->valueOrNull($entry, 'dt'),
                'temp' => $this->valueOrNull($entry, 'temp'),
                'feels_like' => $this->valueOrNull($entry, 'feels_like'),
                'pressure' => $this->valueOrNull($entry, 'pressure'),
                'humidity' => $this->valueOrNull($entry, 'humidity'),
                'dew_point' => $this->valueOrNull($entry, 'dew_point'),
                'uvi' => $this->valueOrNull($entry, 'uvi'),
                'clouds' => $this->valueOrNull($entry, 'clouds'),
                'visibility' => $this->valueOrNull($entry, 'visibility'),
                'wind_speed' => $this->valueOrNull($entry, 'wind_speed'),
                'wind_deg' => $this->valueOrNull($entry, 'wind_deg'),
                'wind_gust' => $this->valueOrNull($entry, 'wind_gust'),
                'weather' => $this->normalizeWeather($entry['weather'] ?? null),
                'pop' => $this->valueOrNull($entry, 'pop'),
            ];
        }

        return $normalized;
    }

    private function normalizeAlerts(array $alerts): array
    {
        $normalized = [];

        foreach ($alerts as $entry) {
            if (!is_array($entry)) {
                continue;
            }

            $normalized[] = [
                'sender_name' => $this->valueOrNull($entry, 'sender_name'),
                'event' => $this->valueOrNull($entry, 'event'),
                'start' => $this->valueOrNull($entry, 'start'),
                'end' => $this->valueOrNull($entry, 'end'),
                'description' => $this->valueOrNull($entry, 'description'),
                'tags' => $this->normalizeTags($entry['tags'] ?? null),
            ];
        }

        return $normalized;
    }

    private function normalizeTags(mixed $tags): ?array
    {
        if (!is_array($tags)) {
            return null;
        }

        return array_values($tags);
    }

    private function normalizeWeather(mixed $weather): array
    {
        if (!is_array($weather)) {
            return [];
        }

        $normalized = [];

        foreach ($weather as $entry) {
            if (!is_array($entry)) {
                continue;
            }

            $normalized[] = [
                'id' => $this->valueOrNull($entry, 'id'),
                'main' => $this->valueOrNull($entry, 'main'),
                'description' => $this->valueOrNull($entry, 'description'),
                'icon' => $this->valueOrNull($entry, 'icon'),
            ];
        }

        return $normalized;
    }

    private function valueOrNull(array $source, string $key): mixed
    {
        if (!array_key_exists($key, $source)) {
            return null;
        }

        return $source[$key];
    }
}
