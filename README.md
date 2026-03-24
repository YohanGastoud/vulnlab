## VulnLab FastAPI Dynamic Router

Application minimaliste pour créer rapidement des routes HTTP configurables via un fichier JSON. Idéale pour des labs de tests d'intrusion.

### Structure
- `app/main.py`: application FastAPI qui charge dynamiquement les routes
- `app/routes.json`: configuration des routes (modifiable à chaud)
- `pyproject.toml`: dépendances gérées avec `uv`
- `Dockerfile`, `docker-compose.yml`: exécution en conteneur

### Démarrage rapide (Docker Compose)
```bash
docker compose up --build
```
Puis ouvrez `http://localhost:8000/` et `http://localhost:8000/test2/cve-4`.

Le `--reload` est activé via Compose et la config `app/routes.json` est montée en volume: toute modification est prise en compte au redémarrage à chaud d’Uvicorn.

### Gestion des dépendances avec uv (recommandé)
- Installer `uv` localement: voir `https://docs.astral.sh/uv/`
- Installer les deps:
```bash
uv sync
```
- Lancer l’app:
```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Ajouter une route
Éditez `app/routes.json` et ajoutez un objet route. Exemple:
```json
{
  "route": "/test2/cve-4",
  "method": "GET",
  "html_output": "\n<h1>content</h1>"
}
```
Champs supportés par route:
- `route` (ou `path`) [string]: chemin, ex `/test2/cve-4`
- `method` [string]: `GET|POST|PUT|PATCH|DELETE|OPTIONS|HEAD` (défaut: `GET`)
- `status_code` [int]: code HTTP (défaut: `200`)
- `headers` [object]: en-têtes additionnels (clé/valeur)
- `html_output` [string]: corps HTML (Content-Type `text/html`)
- `text_output` [string]: corps texte (Content-Type `text/plain`)
- `json_output` [any]: corps JSON (Content-Type `application/json`)
- `content_type` [string]: force un Content-Type spécifique (facultatif)

Remarques:
- S'il y a `html_output`, il est prioritaire sur `text_output`/`json_output`.
- Si seul `json_output` est défini, il est sérialisé tel quel.

### Lancer sans Docker (virtualenv/pip)
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt  # alternatif si vous ne souhaitez pas utiliser uv
export ROUTES_FILE=app/routes.json  # optionnel (défaut)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Variables d’environnement
- `ROUTES_FILE`: chemin du fichier JSON de routes (défaut: `app/routes.json`)

### Santé / Debug
- `GET /__health` -> `{ "status": "ok" }`
- `GET /__config_error__` si la config JSON ne peut pas être chargée (expose l’erreur)

