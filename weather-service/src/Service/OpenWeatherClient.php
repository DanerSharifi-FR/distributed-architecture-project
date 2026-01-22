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
     * @return array{payload: array, upstream_ms: int}
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

        $url = rtrim($this->baseUrl, '/') . '/data/3.0/onecall';
        $query = [
            'lat' => $lat,
            'lon' => $lon,
            'units' => $units,
            'lang' => $lang,
            'exclude' => $exclude,
            'appid' => $this->apiKey,
        ];

        $timeoutSeconds = max(0.0, $this->timeoutMs / 1000);
        $connectTimeoutSeconds = max(0.0, $this->connectTimeoutMs / 1000);
        $attempts = max(0, $this->retries);

        for ($attempt = 0; $attempt <= $attempts; $attempt++) {
            $start = microtime(true);

            try {
                $response = $this->client->request('GET', $url, [
                    'query' => $query,
                    'timeout' => $timeoutSeconds,
                    'connect_timeout' => $connectTimeoutSeconds,
                ]);

                $status = $response->getStatusCode();
                $content = $response->getContent(false);
                $upstreamMs = (int) round((microtime(true) - $start) * 1000);

                if ($status >= 500) {
                    if ($attempt < $attempts) {
                        $this->sleepBackoff($attempt);
                        continue;
                    }

                    throw new OpenWeatherException('Upstream server error');
                }

                if ($status >= 400) {
                    throw new OpenWeatherException('Upstream request rejected');
                }

                $payload = json_decode($content, true);
                if (!is_array($payload)) {
                    throw new OpenWeatherException('Upstream response invalid');
                }

                return [
                    'payload' => $payload,
                    'upstream_ms' => $upstreamMs,
                ];
            } catch (TransportExceptionInterface $exception) {
                if ($attempt < $attempts) {
                    $this->sleepBackoff($attempt);
                    continue;
                }

                throw new OpenWeatherException('Upstream transport error', 0, $exception);
            }
        }

        throw new OpenWeatherException('Upstream request failed');
    }

    private function sleepBackoff(int $attempt): void
    {
        $delayUs = (int) (100000 * (2 ** $attempt));
        usleep($delayUs);
    }
}
