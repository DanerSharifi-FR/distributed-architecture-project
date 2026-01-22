<?php

declare(strict_types=1);

namespace App\Service;

use Symfony\Contracts\HttpClient\Exception\TransportExceptionInterface;
use Symfony\Contracts\HttpClient\HttpClientInterface;

class OpenWeatherClient
{
    public function __construct(
        private readonly HttpClientInterface $client,
        private readonly string $baseUrl,
        private readonly string $apiKey,
        private readonly int $connectTimeoutMs,
        private readonly int $timeoutMs,
        private readonly int $retries
    ) {
    }

    /**
     * @return array{ok: bool, payload?: array, status?: int, error_message?: string, body_snippet?: string, upstream_url_sanitized?: string, upstream_ms: int}
     */
    public function fetchOneCall(
        float $lat,
        float $lon,
        string $units,
        string $lang,
        string $exclude
    ): array {
        if ($this->apiKey === '') {
            throw new \RuntimeException('OpenWeather API key is missing');
        }

        $url = $this->buildOneCallUrl($lat, $lon, $units, $lang, $exclude);
        $sanitizedUrl = $this->sanitize($url);

        $timeoutSeconds = max(0.0, $this->timeoutMs / 1000);
        $connectTimeoutSeconds = max(0.0, $this->connectTimeoutMs / 1000);
        $attempts = max(0, $this->retries);

        for ($attempt = 0; $attempt <= $attempts; $attempt++) {
            $start = microtime(true);

            try {
                $response = $this->client->request('GET', $url, [
                    'timeout' => $timeoutSeconds,
                    'connect_timeout' => $connectTimeoutSeconds,
                ]);

                $status = $response->getStatusCode();
                $content = $response->getContent(false);
                $upstreamMs = (int) round((microtime(true) - $start) * 1000);

                if ($status < 200 || $status >= 300) {
                    if ($status >= 500 && $attempt < $attempts) {
                        $this->sleepBackoff($attempt);
                        continue;
                    }

                    $snippet = $this->sanitize($this->snippet($content));
                    $errorMessage = $this->sanitize($this->extractErrorMessage($content, $status));

                    return [
                        'ok' => false,
                        'status' => $status,
                        'error_message' => $errorMessage,
                        'body_snippet' => $snippet,
                        'upstream_url_sanitized' => $sanitizedUrl,
                        'upstream_ms' => $upstreamMs,
                    ];
                }

                $payload = json_decode($content, true);
                if (!is_array($payload)) {
                    throw new OpenWeatherException('Upstream response invalid');
                }

                return [
                    'ok' => true,
                    'payload' => $payload,
                    'upstream_url_sanitized' => $sanitizedUrl,
                    'upstream_ms' => $upstreamMs,
                ];
            } catch (TransportExceptionInterface $exception) {
                if ($attempt < $attempts) {
                    $this->sleepBackoff($attempt);
                    continue;
                }

                $safeMessage = $this->sanitize($exception->getMessage());
                throw new OpenWeatherException('Upstream transport error: ' . $safeMessage, 0, $exception);
            }
        }

        throw new OpenWeatherException('Upstream request failed');
    }

    private function sleepBackoff(int $attempt): void
    {
        $delayUs = (int) (100000 * (2 ** $attempt));
        usleep($delayUs);
    }

    public function buildOneCallUrl(
        float $lat,
        float $lon,
        string $units,
        string $lang,
        string $exclude
    ): string {
        $query = [
            'lat' => $lat,
            'lon' => $lon,
            'units' => $units,
            'lang' => $lang,
            'appid' => $this->apiKey,
        ];

        if ($exclude !== '') {
            $query['exclude'] = $exclude;
        }

        $base = rtrim($this->baseUrl, '/');

        return $base . '/data/3.0/onecall?' . http_build_query($query);
    }

    public function buildOneCallSanitizedUrl(
        float $lat,
        float $lon,
        string $units,
        string $lang,
        string $exclude
    ): string {
        return $this->sanitize($this->buildOneCallUrl($lat, $lon, $units, $lang, $exclude));
    }

    private function snippet(string $content): string
    {
        $content = trim($content);
        if ($content === '') {
            return '';
        }

        return substr($content, 0, 500);
    }

    private function extractErrorMessage(string $content, int $status): string
    {
        $decoded = json_decode($content, true);
        if (is_array($decoded) && isset($decoded['message']) && is_string($decoded['message'])) {
            return $decoded['message'];
        }

        return sprintf('Upstream returned HTTP %d', $status);
    }

    private function sanitize(string $value): string
    {
        return (string) preg_replace('/(appid=)[^&\\s]+/i', '$1***', $value);
    }
}
