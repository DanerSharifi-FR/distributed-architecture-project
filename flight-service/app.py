import os
import time
import requests
from flask import Flask, jsonify, request

TOKEN_URL = "https://auth.opensky-network.org/auth/realms/opensky-network/protocol/openid-connect/token"
STATES_URL = "https://opensky-network.org/api/states/all"

_cache_data = None
_cache_ts = 0.0
CACHE_TTL_SECONDS = 90

_token = None
_token_expiry_ts = 0.0

app = Flask(__name__)


def get_token():  # récupère un token OAuth2 valide
    global _token
    global _token_expiry_ts

    client_id = os.environ.get("OPENSKY_CLIENT_ID")
    client_secret = os.environ.get("OPENSKY_CLIENT_SECRET")

    if not client_id or not client_secret:
        return None

    now = time.time()
    if _token is not None and now < _token_expiry_ts:
        return _token

    resp = requests.post(
        TOKEN_URL,
        data={
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=10,
    )
    resp.raise_for_status()

    payload = resp.json()
    _token = payload["access_token"]
    expires_in = int(payload.get("expires_in", 1800))
    _token_expiry_ts = now + expires_in - 30
    return _token


def fetch_states_from_opensky(params):  # appelle OpenSky /states/all et renvoie le JSON brut
    token = get_token()
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    resp = requests.get(
        STATES_URL,
        headers=headers,
        params=params,
        timeout=20,
    )

    if resp.status_code == 429:
        retry = int(resp.headers.get("X-Rate-Limit-Retry-After-Seconds", "10"))
        time.sleep(max(1, retry))
        resp = requests.get(STATES_URL, headers=headers, params=params, timeout=20)

    if resp.status_code == 401:
        global _token
        _token = None
        token = get_token()
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        resp = requests.get(STATES_URL, headers=headers, params=params, timeout=20)

    resp.raise_for_status()
    return resp.json()


def normalize_flights(opensky_json):  # transforme le format OpenSky (tableaux) en liste d'objets propres
    states = opensky_json.get("states") or []
    flights = []

    for s in states:
        icao24 = s[0]
        callsign = (s[1] or "").strip()
        origin_country = s[2]
        time_position = s[3]
        last_contact = s[4]
        lon = s[5]
        lat = s[6]
        baro_alt = s[7]
        on_ground = s[8]
        velocity = s[9]
        true_track = s[10]
        vertical_rate = s[11]
        geo_alt = s[13]
        squawk = s[14]
        position_source = s[16]
        category = s[17] if len(s) > 17 else None

        if on_ground is True:
            continue
        if lon is None or lat is None:
            continue

        flights.append({
            "icao24": icao24,
            "callsign": callsign or None,
            "origin_country": origin_country,
            "last_contact": last_contact,
            "time_position": time_position,
            "lon": lon,
            "lat": lat,
            "baro_altitude_m": baro_alt,
            "geo_altitude_m": geo_alt,
            "velocity_mps": velocity,
            "true_track_deg": true_track,
            "vertical_rate_mps": vertical_rate,
            "squawk": squawk,
            "position_source": position_source,
            "category": category,
        })

    return flights


@app.get("/flights")
def get_flights():  # handler Flask
    global _cache_data
    global _cache_ts

    now = time.time()
    if _cache_data is not None and (now - _cache_ts) < CACHE_TTL_SECONDS:
        return jsonify(_cache_data)

    lamin = request.args.get("lamin", type=float)
    lomin = request.args.get("lomin", type=float)
    lamax = request.args.get("lamax", type=float)
    lomax = request.args.get("lomax", type=float)
    extended = request.args.get("extended", default=0, type=int)

    params = {}
    if lamin is not None and lomin is not None and lamax is not None and lomax is not None:
        params["lamin"] = lamin
        params["lomin"] = lomin
        params["lamax"] = lamax
        params["lomax"] = lomax
    if extended == 1:
        params["extended"] = 1

    try:
        opensky_json = fetch_states_from_opensky(params)
        flights = normalize_flights(opensky_json)
    except Exception as e:
        return jsonify({"error": "OpenSky request failed", "details": str(e)}), 502

    _cache_data = flights
    _cache_ts = now
    return jsonify(flights)


def main():  # fonction main()
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "5000"))
    debug = os.environ.get("DEBUG", "0") == "1"
    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    main()
