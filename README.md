# 3hr Take-Home Challenge - Weather + Mood API

**Track:** Back End (SPD)
**Stack:** Python + Flask
**Weather API:** OpenWeatherMap
**Submit:** Slack DM to instructor (not Gradescope)
**Time target:** under 3 hours hands-on (planning does not count)

## What this app does

Anonymous users look up weather by city and log a mood for that day. No login.

## How to run

### 1. Environment

```bash
cp .env.example .env
# edit .env: set OPENWEATHER_API_KEY and REDIS_PASSWORD
```

Do not commit `.env`. Do not bake secrets into the image.

### 2. Local (venv + Redis)

Needs a Redis on `REDIS_URL` (default `redis://localhost:6379/0`). Easiest:

```bash
docker run -d --name mood-redis -p 6380:6379 redis:7.2.5-alpine
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
flask --app wsgi run --host=0.0.0.0 --port=5000
```

- Python used here: 3.13.3 (image uses 3.12.7-slim)
- pip: 26.2.1

### 3. Docker Compose (preferred for graders)

```bash
# needs OPENWEATHER_API_KEY + REDIS_PASSWORD in the environment or local .env
docker compose up --build --detach
curl http://127.0.0.1/health
curl http://127.0.0.1/ready
docker compose down
```

- Public entry: nginx on host port **80** (api is internal-only on 5000)
- Redis: internal only; password via `REDIS_PASSWORD`; AOF on volume `redis-data`
- Container runs **gunicorn** (`wsgi:app`), not `flask run`
- Probes: `/health` = liveness; `/ready` = Redis up (Docker HEALTHCHECK uses `/ready`)
- `PROXY_COUNT=1` on api (nginx sets X-Forwarded-*)
- Rate limits (Flask-Limiter + Redis): default 60/min; `/weather` 30/min; `POST /moods` 20/min; probes exempt

### 4. Quick API checks

```bash
curl "http://127.0.0.1/weather?city=Seattle"

# Post a mood. Server fetches real weather for the city.
# Response includes anon_id; client should store it for future requests.
curl -X POST http://127.0.0.1/moods \
  -H "Content-Type: application/json" \
  -d '{"mood":"happy","city":"Seattle"}'

# List your moods (scoped to your anon_id via X-Anon-Id header)
curl -H "X-Anon-Id: <id-from-post>" http://127.0.0.1/moods
```

### 5. Tests

```bash
source .venv/bin/activate
pytest
```

Requires Redis running on `localhost:6380` (tests use real Redis in db 1).
Weather HTTP calls are mocked. No OpenWeather API key needed; uses separate test Redis DB.

### 6. CLI Commands

Executable scripts for development:

```bash
./start              # Start Docker Redis, Flask, run tests
./start -t           # Start but skip tests
./start -d           # Skip Docker, use system Redis
./start -v           # Verbose output
./start -h           # Show help

./restart            # Clean restart (kill all, start fresh)
./restart -t         # Restart but skip tests
./restart -v         # Verbose

./end                # Stop all services and cleanup
./end -v             # Verbose
```

Each command supports `-h` for help and `-v` for verbose output.
For Docker flag details: `./start -h`

## Time log

PDT. Clock started when I made the venv (around 14:13). Planning before that is just setup.

### 2026-09-30

- 13:58 scanned the empty repo. put project notes + this log in the README. left `.gitignore` alone.
- 14:11 dropped an empty `requirements.txt` placeholder. will freeze real pins after installs.
- 14:13 made `.venv` (Python 3.13.3), bumped pip to 26.2.1. this is where I start counting hands-on time.
- 14:14 installed Flask 3.1.3
- 14:15 installed requests 2.34.2
- 14:17 installed pytest 9.1.1 (pinning exact versions so her machine matches mine)
- 14:19 installed pre-commit, bandit, pip-audit. wrote `.pre-commit-config.yaml`, ran `pre-commit install`. EOF hook tried to edit `.gitignore` so I reverted that and excluded it. also added `.github/workflows/security.yml`.
- 14:23 hooked pip-audit into pre-commit + CI with `--strict`. ran it locally, clean so far.
- 14:25 added both gitleaks and trufflehog jobs in CI
- 14:27 installed python-dotenv, froze full `requirements.txt` from the venv, re-ran pip-audit (still clean)
- 14:30 decided moods go in Redis, not a JSON file. installed redis-py 8.1.0, re-froze. means Compose will need a redis service later.
- 14:31 logged into OpenWeather and started wiring the API key
- 14:33 made `.env` + `.env.example` skeletons (`OPENWEATHER_API_KEY`, `REDIS_URL`, host/port)
- 14:37 put the real key in local `.env` (gitignored, not committed)
- 14:44 made `app/` + `tests/unit/`, wrote weather + mood unit tests with mocks. `pytest` -> 14 passed.
- 14:51 added `wsgi.py` (load dotenv, `app = create_app()`). used `wsgi.py` instead of `app.py` so it does not clash with the `app/` package.
- 14:55 wired Redis in `create_app` via `redis.Redis.from_url(REDIS_URL)` onto `app.extensions["redis"]` (decode_responses, protocol=2). tests can still inject `REDIS_CLIENT`. `/health` now reports `redis` true/false.
- 15:03 started Redis with Docker: `docker run -d --name mood-redis -p 6379:6379 redis:7-alpine`. ping -> PONG. `/health` -> `{"status":"ok","redis":true}`.
- 15:04 added route tests under `tests/functional/`. conftest injects a mock Redis. `pytest` -> 21 passed.
- 15:07 added `Dockerfile` (`python:3.12.7-slim`), `.dockerignore`, `compose.yaml` (api + `redis:7.2.5-alpine`). `docker compose up --build -d` then `curl /health` -> ok.
- 15:08 rewrote How to run in the README (env, local venv, Compose, curl checks, pytest).
- 15:10 set redis-py timeouts on `from_url`: `socket_connect_timeout=2`, `socket_timeout=2`, `health_check_interval=30`.
- 15:11 Compose smoke: moods OK; `/weather` failed because One Call 4.0 needs a paid plan. switched to Current Weather Data 2.5. `pytest` 21 passed. rebuild smoke green.
- 15:14 switched container CMD to `gunicorn==23.0.0` (`wsgi:app`, exec form / PID 1). local venv still uses `flask run`.
- 15:16 run container as non-root user `app` (uid/gid 1000).
- 15:18 Docker HEALTHCHECK on `/ready` via stdlib urllib.
- 15:19 redis healthcheck + api `depends_on` `service_healthy`.
- 15:22 Redis `--requirepass` + AOF on volume `redis-data`. api `REDIS_URL` includes password.
- 15:24 `list_moods` uses `scan_iter` instead of `KEYS`.
- 15:28 split probes: `/health` liveness, `/ready` Redis readiness (503 if down).
- 15:31 Compose resource limits on api and redis.
- 15:33 ProxyFix gated by `PROXY_COUNT` (Compose sets 1 behind nginx).
- 15:36 nginx reverse proxy on port 80; api internal-only.
- 15:39 structured JSON logs via `python-json-logger` + `gunicorn.conf.py`.
- 15:48 Flask-Limiter with Redis storage. default 60/min; weather 30/min; POST moods 20/min; probes exempt.

About 95 min since the venv (14:13 → 15:48).

## Design decisions

- **Storage:** Redis (db 0 for dev, db 1 for tests; auto-cleanup between tests).
- **Anonymous users:** X-Anon-Id header (auto-generated UUID or explicit); mood keys scoped per user: `moods:{anon_id}:{date}`.
- **Weather:** Server fetches via OpenWeatherMap 2.5 API; client sends only city, server stores snapshot.
- **One mood per day:** Overwrite by default (can reject with `overwrite=False`).
- **Docker:** Compose with `api` + `redis`; nginx reverse proxy; gunicorn container.
- **Endpoints:** `GET /health`, `GET /ready`, `GET /weather?city=`, `POST /moods`, `GET /moods`.
- **Rate limits:** 60/min default; 30/min `/weather`; 20/min `POST /moods`; health/ready exempt.

## Project structure

```
app/
  factory.py          # Flask app initialization, Redis/limiter config
  routes.py           # 5 endpoints: health, ready, weather, POST/GET moods
  weather.py          # OpenWeatherMap 2.5 API client
  moods.py            # Redis mood storage, per-user isolation
  extensions.py       # Flask-Limiter instance (Redis-backed)

tests/
  conftest.py         # Real Redis fixtures (db 1, auto-cleanup)
  unit/               # weather.py, moods.py unit tests
  functional/         # routes.py integration tests

nginx/
  default.conf        # 80→5000 routing

.github/workflows/
  security.yml        # CI: bandit, pip-audit, gitleaks, trufflehog

Dockerfile            # Python 3.12.7-slim, gunicorn entry
compose.yaml          # api + redis services, nginx reverse proxy
gunicorn.conf.py      # JSON structured logging
wsgi.py               # Entry point for gunicorn (dotenv + create_app)
requirements.txt      # Pinned dependencies (31 total)
.pre-commit-config.yaml  # bandit, gitleaks, trufflehog, pip-audit
```

## Key fixes applied

1. **Server-side weather fetching** (routes.py:62-68)
   - Before: Client sent weather in request body (trusted client data)
   - After: Server calls `weather_for_city(city)`, stores real snapshot
   - API now simple: `{"mood":"happy","city":"Seattle"}`

2. **Per-user mood isolation** (moods.py, routes.py)
   - Before: Redis key `moods:{day}` (all users shared one record)
   - After: `moods:{anon_id}:{day}` (each user isolated)
   - X-Anon-Id header: UUID auto-generated or explicit client ID
   - GET /moods scans only user's moods when header provided

3. **Real Redis in tests** (conftest.py, test_routes.py)
   - Before: MagicMock Redis (fast but unrealistic)
   - After: Real `redis.Redis` on db 1 (true integration test)
   - Auto-cleanup (`flushdb()`) between tests
   - Graceful skip if Redis unavailable

## Endpoints

### GET /health
Liveness probe (process is up).
```
curl http://localhost:5000/health
{"status": "ok"}
```

### GET /ready
Readiness probe (Redis up, or 503).
```
curl http://localhost:5000/ready
{"status": "ready", "redis": true}
```

### GET /weather?city=<city>
Fetch weather snapshot (30/min rate limit).
```
curl "http://localhost:5000/weather?city=Seattle"
{
  "city": "Seattle",
  "country": "US",
  "lat": 47.6,
  "lon": -122.3,
  "weather": {"temp": 12.0, "main": "Rain", "description": "light rain"}
}
```

### POST /moods
Log a mood + city (server fetches weather, 20/min rate limit, 201 Created).
```
curl -X POST http://localhost:5000/moods \
  -H "Content-Type: application/json" \
  -d '{"mood":"happy","city":"Seattle"}'
{
  "mood": "happy",
  "city": "Seattle",
  "date": "2026-10-06",
  "weather": {...},
  "anon_id": "550e8400-e29b-41d4-a716-446655440000",
  "saved_at": "2026-10-06T20:48:23.837627+00:00"
}
```

Or with explicit X-Anon-Id header:
```
curl -X POST http://localhost:5000/moods \
  -H "X-Anon-Id: user-123" \
  -H "Content-Type: application/json" \
  -d '{"mood":"happy","city":"Seattle"}'
```

### GET /moods
List moods (all if no header, or scoped to X-Anon-Id).
```
# All moods across all users
curl http://localhost:5000/moods

# Only user's moods
curl -H "X-Anon-Id: 550e8400-e29b-41d4-a716-446655440000" http://localhost:5000/moods
[
  {"mood": "happy", "city": "Seattle", "date": "2026-10-06", "weather": {...}, ...}
]
```

## Test coverage

- **Unit tests:** weather.py, moods.py logic (mocked HTTP, real Redis)
- **Functional tests:** routes.py endpoints, anon_id isolation, rate limiting
- **Real Redis:** Integration tests use separate db (db 1); auto-cleanup
- **31 total:** All passing, no external dependencies except Redis

Run:
```bash
pytest -v --tb=short
```

## CI/CD

GitHub Actions on push/PR:
- **gitleaks:** Detect secrets
- **trufflehog:** Scan for leaked credentials (verified + unknown)
- **bandit:** Python security linter
- **pip-audit:** Dependency vulnerabilities (--strict)

All pass. No security issues or known CVEs.
