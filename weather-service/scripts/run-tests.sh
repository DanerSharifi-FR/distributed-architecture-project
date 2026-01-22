#!/usr/bin/env bash
set -eu

report_dir="tests/reports"
report_file="${report_dir}/phpunit-report.md"
testdox_file="${report_dir}/testdox.txt"
junit_file="${report_dir}/junit.xml"
mkdir -p "${report_dir}"

set +e
vendor/bin/phpunit --testdox-text "${testdox_file}" --log-junit "${junit_file}"
status=$?
set -e

tmp_file="${report_file}.tmp"
{
  echo "# PHPUnit Report"
  echo
  echo "Generated at: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo
  echo "## TestDox"
  echo
  if [ -s "${testdox_file}" ]; then
    cat "${testdox_file}"
  else
    echo "(no TestDox output found)"
  fi
  echo
  echo "## Test Summary"
  php -r '
$xml = simplexml_load_file($argv[1]);
if ($xml === false) {
    echo "Unable to parse JUnit XML\n";
    exit(0);
}
$attrs = $xml->testsuite->testsuite["tests"] ? $xml->testsuite->testsuite["tests"] : $xml["tests"];
$assertions = $xml->testsuite->testsuite["assertions"] ? $xml->testsuite->testsuite["assertions"] : $xml["assertions"];
$failures = $xml->testsuite->testsuite["failures"] ? $xml->testsuite->testsuite["failures"] : $xml["failures"];
$errors = $xml->testsuite->testsuite["errors"] ? $xml->testsuite->testsuite["errors"] : $xml["errors"];
$skipped = $xml->testsuite->testsuite["skipped"] ? $xml->testsuite->testsuite["skipped"] : $xml["skipped"];
echo "tests: {$attrs}\nassertions: {$assertions}\nfailures: {$failures}\nerrors: {$errors}\nskipped: {$skipped}\n";
' "${junit_file}"
  echo
  echo "## Live API Responses"
  echo
  if [ "${RUN_LIVE_API:-}" != "1" ]; then
    echo "Live API checks skipped (set RUN_LIVE_API=1 to enable)."
  else
    lat="${OPENWEATHER_LIVE_LAT:-43.6}"
    lon="${OPENWEATHER_LIVE_LON:-1.44}"
    lang="${OPENWEATHER_LIVE_LANG:-en}"
    units="metric"
    raw="0"
    exclude=""

  pretty_print() {
    php -r '
$input = stream_get_contents(STDIN);
$decoded = json_decode($input, true);
if ($decoded === null && json_last_error() !== JSON_ERROR_NONE) {
    echo $input;
    exit(0);
}
echo json_encode($decoded, JSON_PRETTY_PRINT);
'
  }

  fetch_and_print() {
    label="$1"
    url="$2"
    sanitized_url="$3"
    header="$4"

    if [ -n "${header}" ]; then
      response="$(curl -sS -H "${header}" -w '\n%{http_code}' "${url}" || true)"
    else
      response="$(curl -sS -w '\n%{http_code}' "${url}" || true)"
    fi
    status_code="$(printf '%s' "${response}" | tail -n 1)"

    echo
    echo "### ${label}"
    echo
    echo "- status: ${status_code}"
    echo "- upstream_url_sanitized: ${sanitized_url}"
  }

    echo "### Service /v1/onecall (minimal)"
    if [ -z "${WEATHER_SERVICE_BASE_URL:-}" ]; then
      service_base="http://localhost:8080"
    else
      service_base="${WEATHER_SERVICE_BASE_URL}"
    fi
    token_header=""
    if [ -n "${INTERNAL_TOKEN:-}" ]; then
      token_header="X-Internal-Token: ${INTERNAL_TOKEN}"
    fi

    query="lat=${lat}&lon=${lon}&units=${units}&lang=${lang}&raw=${raw}"
    url="${service_base%/}/v1/onecall?${query}"
    sanitized_url="${url}"
    fetch_and_print "units=${units} raw=${raw} exclude=none" "${url}" "${sanitized_url}" "${token_header}"

    echo
    echo "### OpenWeather /data/3.0/onecall (minimal)"
    if [ -z "${OPENWEATHER_API_KEY:-}" ]; then
      echo "OPENWEATHER_API_KEY not set; OpenWeather live responses skipped."
    else
      base_url="${OPENWEATHER_BASE_URL:-https://api.openweathermap.org}"
      query="lat=${lat}&lon=${lon}&units=${units}&lang=${lang}&appid=${OPENWEATHER_API_KEY}"
      url="${base_url%/}/data/3.0/onecall?${query}"
      sanitized_url="$(printf '%s' "${url}" | sed 's/appid=[^&]*/appid=***/')"
      fetch_and_print "units=${units} exclude=none" "${url}" "${sanitized_url}" ""
    fi
  fi
} > "${tmp_file}"

mv "${tmp_file}" "${report_file}"
echo "Report written to ${report_file}"

exit "${status}"
