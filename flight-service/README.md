# OpenSky Flight Service (Flask)

Petit microservice Flask qui **surcouche** l’API OpenSky et expose un endpoint unique :

- `GET /flights` → renvoie **une liste JSON** d’avions **en vol** (on enlève `on_ground = true` et on ignore les positions manquantes).

Le service utilise OpenSky `GET /api/states/all` (snapshot “live” des positions). 

---

## Prérequis

- Python 3.10+ (recommandé)
- Un accès Internet
- (Optionnel) Un compte OpenSky + un **API client** si tu veux le mode authentifié (OAuth2). citeturn1view0turn1view1

---

## Installation & exécution (local)

Dans le dossier qui contient `app.py` et `requirements.txt` :

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Ça démarre sur `http://localhost:5000`.

---

## Tester rapidement (sans Insomnia)

### Global (monde entier)
```bash
curl -s "http://localhost:5000/flights" | head
```

### Zone limitée (bounding box)
Exemple autour de Nantes :

```bash
curl -s "http://localhost:5000/flights?lamin=46.9&lomin=-2.3&lamax=47.5&lomax=-1.2" | head
```

### Extended (catégorie d’aéronef)
```bash
curl -s "http://localhost:5000/flights?extended=1" | head
```

> `extended=1` demande à OpenSky d’inclure `category` (catégorie d’aéronef) dans le state vector. 

---

## Import Insomnia

Importe le fichier YAML fourni :

- `insomnia-opensky-flight-service.yaml`

Puis lance :
- **GET flights (global)**
- **GET flights (bbox Nantes)**
- **GET flights (extended=1)**

Aucune variable d’environnement n’est utilisée dans le fichier Insomnia (tout pointe sur `http://localhost:5000`).

---

## API exposée

### `GET /flights`

**Query params (optionnels)**

- `lamin`, `lomin`, `lamax`, `lomax` : bounding box (lat/lon) pour limiter la zone
- `extended=1` : inclut `category` si disponible

**Réponse**
Une **liste** d’objets (pas d’enveloppe), typiquement :

```json
[
  {
    "icao24": "3c6444",
    "callsign": "DLH123",
    "origin_country": "Germany",
    "last_contact": 1736420000,
    "time_position": 1736420000,
    "lon": 2.35,
    "lat": 48.86,
    "baro_altitude_m": 10500.0,
    "geo_altitude_m": 10600.0,
    "velocity_mps": 230.5,
    "true_track_deg": 180.0,
    "vertical_rate_mps": 0.0,
    "squawk": "1234",
    "position_source": 0,
    "category": 0
  }
]
```

---

## Mode anonyme vs authentifié (OpenSky) — limitations importantes

OpenSky fonctionne avec un système de **crédits** + des limites de fréquence.  
Le service met en place un **cache** (par défaut 90s) pour éviter de cramer tes crédits.

### 1) Mode anonyme (sans auth)

C’est le mode le plus simple : **aucun token** / aucun header `Authorization`.

Limites (OpenSky) : 
- Résolution temporelle : **10 secondes**
- Quota : **400 crédits / jour**
- Coût `/states/all` :
  - **1 à 4 crédits** selon la taille de la zone (par “square degrees”)
  - **global = 4 crédits** 

➡️ Conclusion : en global, tu tiens ~`400 / 4 = 100` requêtes / jour. Donc **cache indispensable**.

### 2) Mode authentifié (OpenSky user / API client)

Si tu utilises un compte OpenSky (ou API client), tu as : 
- Quota : **4000 crédits / jour**
- Historique : jusqu’à **1 heure** dans le passé (via `time`)
- Résolution temporelle : **5 secondes**
- Les contributeurs (récepteur ADS-B ≥ 30% online) montent à **8000 crédits / jour**. 

### Rate limit / erreurs

Quand tu dépasses la limite, OpenSky renvoie : 
- `429 Too Many Requests`
- header `X-Rate-Limit-Retry-After-Seconds` (combien de secondes attendre)
- header `X-Rate-Limit-Remaining` (crédits restants)

Ton code gère un `429` en attendant puis en retentant une fois.

---

## Forcer le mode anonyme

Deux options :

1) **Ne mets pas** `OPENSKY_CLIENT_ID` / `OPENSKY_CLIENT_SECRET` dans ton environnement → le code n’ajoute pas `Authorization`.

2) Si tu as ajouté le flag dans `app.py` :
```python
FORCE_ANONYMOUS = True
```
Alors **même si** quelqu’un a des variables d’environnement, l’app restera anonyme.

---

## Activer le mode authentifié (OAuth2)

Si tu veux (et si ton code n’est pas forcé en anonyme), configure :

- `OPENSKY_CLIENT_ID`
- `OPENSKY_CLIENT_SECRET`

Ces identifiants viennent d’un **API client** créé sur ton compte OpenSky. citeturn1view0turn1view1

Exemple (Linux/macOS) :

```bash
export OPENSKY_CLIENT_ID="..."
export OPENSKY_CLIENT_SECRET="..."
python app.py
```

Le token OAuth2 expire après ~**30 minutes** (le code le régénère). 

---

## Docker

### Build

```bash
docker build -t opensky-flight-service .
```

### Run (anonyme)

```bash
docker run --rm -p 5000:5000 opensky-flight-service
```

### Run (authentifié)

```bash
docker run --rm -p 5000:5000   -e OPENSKY_CLIENT_ID="..."   -e OPENSKY_CLIENT_SECRET="..."   opensky-flight-service
```

⚠️ Si `FORCE_ANONYMOUS=True` dans le code, les variables ci-dessus seront ignorées.


## Fichiers

- `app.py` : service Flask
- `requirements.txt` : dépendances
- `Dockerfile` : build + run Docker
- `insomnia-opensky-flight-service.yaml` : collection Insomnia