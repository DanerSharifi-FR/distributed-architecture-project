import os  # lire les variables d'environnement
import time  # gérer cache + expiration token
import requests  # appeler OpenSky en HTTP
from flask import Flask, jsonify, request  # API Flask + JSON + query params

# --- URLs OpenSky (officiel) ---
TOKEN_URL = "https://auth.opensky-network.org/auth/realms/opensky-network/protocol/openid-connect/token"  # endpoint OAuth2 token
STATES_URL = "https://opensky-network.org/api/states/all"  # endpoint positions (snapshot)

# --- Cache (pour ne pas spammer OpenSky) ---
CACHE_TTL_SECONDS = 90  # 90–120s recommandé si tu prends le monde entier
_cache_data = None  # cache: dernière liste "flights" renvoyée
_cache_ts = 0.0  # cache: timestamp du dernier remplissage

# --- Token OAuth2 (pour comptes récents) ---
_token = None  # token en mémoire
_token_expiry_ts = 0.0  # timestamp d'expiration du token

# --- Flask app ---
app = Flask(__name__)  # création de l'app Flask


def get_token():  # récupère un token OAuth2 valide (ou en redemande un)
    global _token  # on modifie la variable globale _token
    global _token_expiry_ts  # on modifie la variable globale _token_expiry_ts

    client_id = os.environ.get("OPENSKY_CLIENT_ID")  # lit OPENSKY_CLIENT_ID (ou None si absent)
    client_secret = os.environ.get("OPENSKY_CLIENT_SECRET")  # lit OPENSKY_CLIENT_SECRET (ou None si absent)

    if not client_id or not client_secret:  # si pas de credentials
        return None  # on fera une requête sans auth (quota faible, mais ça marche)

    now = time.time()  # temps actuel
    if _token is not None and now < _token_expiry_ts:  # si token présent et pas expiré
        return _token  # on le réutilise

    resp = requests.post(  # POST OAuth2 client_credentials
        TOKEN_URL,  # endpoint token
        data={  # payload OAuth2
            "grant_type": "client_credentials",  # flux client_credentials
            "client_id": client_id,  # id client
            "client_secret": client_secret,  # secret client
        },  # fin payload
        headers={"Content-Type": "application/x-www-form-urlencoded"},  # format standard
        timeout=10,  # timeout réseau
    )  # fin POST
    resp.raise_for_status()  # crash propre si erreur HTTP

    payload = resp.json()  # parse JSON
    _token = payload["access_token"]  # récupère le token
    expires_in = int(payload.get("expires_in", 1800))  # durée (souvent 1800s)
    _token_expiry_ts = now + expires_in - 30  # expiration avec marge
    return _token  # renvoie le token


def fetch_states_from_opensky(params):  # appelle OpenSky /states/all et renvoie le JSON brut
    token = get_token()  # récupère token (ou None)
    headers = {}  # headers HTTP
    if token:  # si on a un token
        headers["Authorization"] = f"Bearer {token}"  # auth Bearer

    resp = requests.get(  # appel à OpenSky
        STATES_URL,  # endpoint
        headers=headers,  # headers (avec ou sans auth)
        params=params,  # query params (bbox, extended, etc.)
        timeout=20,  # timeout
    )  # fin GET

    if resp.status_code == 429:  # rate limit atteint
        retry = int(resp.headers.get("X-Rate-Limit-Retry-After-Seconds", "10"))  # délai conseillé (sinon 10s)
        time.sleep(max(1, retry))  # on attend
        resp = requests.get(STATES_URL, headers=headers, params=params, timeout=20)  # on réessaie une fois

    if resp.status_code == 401:  # token expiré/invalide
        global _token  # on va invalider le token
        _token = None  # force un refresh
        token = get_token()  # redemande un token
        headers = {}  # recrée headers
        if token:  # si token OK
            headers["Authorization"] = f"Bearer {token}"  # remet auth
        resp = requests.get(STATES_URL, headers=headers, params=params, timeout=20)  # réessaie

    resp.raise_for_status()  # erreur HTTP => exception
    return resp.json()  # renvoie JSON OpenSky


def normalize_flights(opensky_json):  # transforme le format OpenSky (tableaux) en liste d'objets propres
    states = opensky_json.get("states") or []  # récupère la liste des state vectors
    flights = []  # liste finale des avions "en vol"

    for s in states:  # s = tableau avec indices OpenSky
        # Indices OpenSky (cf doc): 0=icao24, 1=callsign, 2=origin_country, 3=time_position, 4=last_contact,
        # 5=longitude, 6=latitude, 7=baro_altitude, 8=on_ground, 9=velocity, 10=true_track, 11=vertical_rate,
        # 12=sensors, 13=geo_altitude, 14=squawk, 15=spi, 16=position_source, 17=category
        icao24 = s[0]  # identifiant transpondeur
        callsign = (s[1] or "").strip()  # callsign (souvent avec espaces)
        origin_country = s[2]  # pays d'origine
        time_position = s[3]  # dernier update position
        last_contact = s[4]  # dernier message quelconque
        lon = s[5]  # longitude
        lat = s[6]  # latitude
        baro_alt = s[7]  # altitude baro (m)
        on_ground = s[8]  # au sol ?
        velocity = s[9]  # vitesse sol (m/s)
        true_track = s[10]  # cap (degrés)
        vertical_rate = s[11]  # vario (m/s)
        geo_alt = s[13]  # altitude géométrique (m)
        squawk = s[14]  # squawk
        position_source = s[16]  # source position
        category = s[17] if len(s) > 17 else None  # catégorie (présent si extended=1)

        if on_ground is True:  # si au sol
            continue  # on ne veut que "en vol"
        if lon is None or lat is None:  # si pas de position exploitable
            continue  # on ignore

        flights.append({  # on ajoute un objet "clean"
            "icao24": icao24,  # id unique
            "callsign": callsign or None,  # callsign (None si vide)
            "origin_country": origin_country,  # pays
            "last_contact": last_contact,  # timestamp
            "time_position": time_position,  # timestamp
            "lon": lon,  # longitude
            "lat": lat,  # latitude
            "baro_altitude_m": baro_alt,  # altitude baro
            "geo_altitude_m": geo_alt,  # altitude geo
            "velocity_mps": velocity,  # vitesse
            "true_track_deg": true_track,  # cap
            "vertical_rate_mps": vertical_rate,  # vario
            "squawk": squawk,  # squawk
            "position_source": position_source,  # source position
            "category": category,  # catégorie (si demandée)
        })  # fin objet

    return flights  # renvoie la liste


@app.get("/flights")  # route GET /flights
def get_flights():  # handler Flask
    global _cache_data  # on utilise le cache global
    global _cache_ts  # idem

    now = time.time()  # temps actuel
    if _cache_data is not None and (now - _cache_ts) < CACHE_TTL_SECONDS:  # cache valide ?
        return jsonify(_cache_data)  # renvoie direct la liste en JSON

    # Query params optionnels (bbox + extended)
    lamin = request.args.get("lamin", type=float)  # min latitude
    lomin = request.args.get("lomin", type=float)  # min longitude
    lamax = request.args.get("lamax", type=float)  # max latitude
    lomax = request.args.get("lomax", type=float)  # max longitude
    extended = request.args.get("extended", default=0, type=int)  # 1 pour inclure category

    params = {}  # params OpenSky
    if lamin is not None and lomin is not None and lamax is not None and lomax is not None:  # bbox complète ?
        params["lamin"] = lamin  # ajoute lamin
        params["lomin"] = lomin  # ajoute lomin
        params["lamax"] = lamax  # ajoute lamax
        params["lomax"] = lomax  # ajoute lomax
    if extended == 1:  # si on veut category
        params["extended"] = 1  # active category côté OpenSky

    try:  # on encapsule pour renvoyer une erreur API propre
        opensky_json = fetch_states_from_opensky(params)  # appel OpenSky brut
        flights = normalize_flights(opensky_json)  # filtre + format "en vol"
    except Exception as e:  # n'importe quelle erreur réseau/auth/parsing
        return jsonify({"error": "OpenSky request failed", "details": str(e)}), 502  # erreur côté backend externe

    _cache_data = flights  # met en cache
    _cache_ts = now  # timestamp cache
    return jsonify(flights)  # renvoie la liste JSON


def main():  # fonction main() comme tu veux
    host = os.environ.get("HOST", "0.0.0.0")  # host par défaut
    port = int(os.environ.get("PORT", "5000"))  # port par défaut
    debug = os.environ.get("DEBUG", "0") == "1"  # debug si DEBUG=1
    app.run(host=host, port=port, debug=debug)  # démarre Flask


if __name__ == "__main__":  # exécution directe
    main()  # appelle main()
