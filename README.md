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
docker run -d --name mood-redis -p 6379:6379 redis:7.2.5-alpine
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
curl -X POST http://127.0.0.1/moods \
  -H "Content-Type: application/json" \
  -d '{"mood":"ok","note":"cloudy"}'
curl http://127.0.0.1/moods
```

### 5. Tests

```bash
source .venv/bin/activate
pytest
```

Weather HTTP and Redis are mocked. No API key and no Redis needed for `pytest`.

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

About 150 min since the venv.

## Open decisions

- Storage: Redis (decided). Mood entries live in Redis. Tests mock Redis.
- One mood per day: overwrite by default (can reject with overwrite=False).
- Docker: Compose with `api` + `redis` (done).
- Endpoints: `GET /health`, `GET /ready`, `GET /weather?city=`, `POST /moods`, `GET /moods`.
