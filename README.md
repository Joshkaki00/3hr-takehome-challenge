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

PDT. Clock for the build started when I made the venv (around 14:13). Planning before that is just setup.

### 2026-09-30

- 13:58 scanned the empty repo. put project notes + this log in the README (instructor wants everything here). left `.gitignore` alone.
- 14:01 flipped through Flask / pytest / requests / OpenWeather docs so I am not guessing later.
- 14:09 same idea, reading docs as a checklist before writing code.
- 14:11 dropped an empty `requirements.txt` placeholder. will freeze real pins after installs.
- 14:13 made `.venv` (Python 3.13.3), bumped pip to 26.2.1. this is where I start counting hands-on time.
- 14:14 installed Flask 3.1.3
- 14:15 installed requests 2.34.2
- 14:17 installed pytest 9.1.1 (pinning exact versions so her machine matches mine)
- 14:18 looked up how people usually do pre-commit + GH security checks
- 14:19 installed pre-commit, bandit, pip-audit. wrote `.pre-commit-config.yaml`, ran `pre-commit install`. EOF hook tried to edit `.gitignore` so I reverted that and excluded it. also added `.github/workflows/security.yml`.
- 14:23 hooked pip-audit into pre-commit + CI with `--strict`. ran it locally, clean so far.
- 14:25 added both gitleaks and trufflehog jobs in CI (gitleaks is quick, trufflehog checks harder)
- 14:27 installed python-dotenv, froze full `requirements.txt` from the venv, re-ran pip-audit (still clean)
- 14:30 decided moods go in Redis, not a JSON file. installed redis-py 8.1.0, re-froze. means Compose will need a redis service later.
- 14:31 logged into OpenWeather and started wiring the API key
- 14:33 made `.env` + `.env.example` skeletons (`OPENWEATHER_API_KEY`, `REDIS_URL`, host/port)
- 14:37 put the real key in local `.env` (gitignored, not committed)
- 14:38 redid this time log. the big table looked fake. switching to timestamp bullets like a normal work journal.
- 14:44 looked up how people structure Flask tests (app factory, `tests/conftest.py`, `tests/unit/`). made `app/` + `tests/unit/`, wrote weather + mood unit tests with mocks. `pytest` -> 14 passed.
- 14:50 re-read OpenWeather One Call 4.0 + Flask quickstart (minimal app, `flask --app ... run`, `--host=0.0.0.0`). next step is making the runnable app entry, one piece at a time.
- 14:51 added `wsgi.py` (load dotenv, `app = create_app()`). used `wsgi.py` instead of `app.py` so it does not clash with the `app/` package. run with `flask --app wsgi run` (or just `flask run` from this dir).
- 14:55 read redis-cli docs (`ping`, `-u redis://host:port/db`). wired Redis in `create_app` via `redis.Redis.from_url(REDIS_URL)` onto `app.extensions["redis"]` (decode_responses, protocol=2). tests can still inject `REDIS_CLIENT`. `/health` now reports `redis` true/false. note: `redis-cli` is not installed on this machine yet; server will come with Compose later.
- 15:00 read redis-py client guide. matches what we already do: `decode_responses=True`, SET/GET strings (or hashes). needs a running Redis server. optional `redis[hiredis]` for faster parsing later.
- 15:01 read redis-py production usage notes: retries (default 3), `health_check_interval`, timeouts (`socket_connect_timeout` / `socket_timeout`), handle `ConnectionError`/`TimeoutError`. good candidates to tighten on `from_url` later if we have time.
- 15:03 started Redis with Docker: `docker run -d --name mood-redis -p 6379:6379 redis:7-alpine`. `redis-cli ping` inside container -> PONG. hit `/health` via test client -> `{"status":"ok","redis":true}`.
- 15:04 added route tests under `tests/functional/` (`/health`, `/weather`, `/moods`). conftest now injects a mock Redis so tests do not need a live server. `pytest` -> 21 passed.
- 15:06 re-read Docker run-an-app tutorial, `docker version`, CLI ref, Compose secrets docs. kept API key as env (not Compose secrets file) for simpler instructor setup.
- 15:07 added `Dockerfile` (`python:3.12.7-slim`), `.dockerignore`, `compose.yaml` (api + `redis:7.2.5-alpine`). `docker compose up --build -d` then `curl /health` -> `{"status":"ok","redis":true}`.
- 15:08 rewrote How to run in the README (env, local venv, Compose, curl checks, pytest). stub "Filled in after the app exists" is gone.
- 15:10 set redis-py timeouts on `from_url`: `socket_connect_timeout=2`, `socket_timeout=2`, `health_check_interval=30`.
- 15:11 Compose smoke: moods OK; `/weather` returned invalid key. root cause: One Call 4.0 needs a paid plan. switched to Current Weather Data 2.5 (free). updated unit mocks. `pytest` 21 passed. rebuild smoke: Seattle weather + POST/GET moods all green.
- 15:14 prod step 1 (web search): Flask says use a real WSGI server, not `flask run`. installed `gunicorn==23.0.0`, pinned in requirements, Dockerfile CMD now `gunicorn -w 2 -b 0.0.0.0:5000 wsgi:app` (exec form so gunicorn is PID 1). local venv still uses `flask run`.
- 15:16 prod step 2 (web search): run container as non-root. Dockerfile adds system user/group `app` (uid/gid 1000), `chown` app files, `USER app` before gunicorn.
- 15:18 prod step 3 (web search): Docker HEALTHCHECK on `/health` via stdlib urllib (slim has no curl). interval 30s, start-period 10s.
- 15:19 prod step 4 (web search): Compose waits for Redis ready. redis `healthcheck: redis-cli ping`, api `depends_on.redis.condition: service_healthy`.
- 15:22 prod step 5 (web search): Redis `--requirepass` + AOF (`appendonly yes`, volume `redis-data`). healthcheck uses `REDISCLI_AUTH` (no `-a` on CLI). api `REDIS_URL` includes password. `.env.example` documents `REDIS_PASSWORD`.
- 15:24 prod step 6 (web search): Redis anti-pattern KEYS -> `scan_iter(match="moods:*")` in `list_moods`. unit test updated.
- 15:28 prod step 7 (web search): split probes. `/health` liveness (always 200). `/ready` checks Redis, 503 if down. Docker HEALTHCHECK now hits `/ready`.
- 15:31 prod step 8 (web search): Compose `deploy.resources` limits/reservations on api (1 CPU / 256M) and redis (0.5 CPU / 128M). Compose V2 applies these without Swarm.
- 15:33 prod step 9 (web search): Flask ProxyFix gated by `PROXY_COUNT` (default 0). Only wrap when behind a real proxy; count must match the chain.
- 15:36 prod step 10 (web search): nginx reverse proxy (`nginx:1.27.3-alpine`) on port 80. api no longer published; sets X-Forwarded-*. Compose forces `PROXY_COUNT=1`.
- 15:39 prod step 11 (web search): structured JSON logs. pinned `python-json-logger==4.2.0`, `gunicorn.conf.py` `logconfig_dict`, Dockerfile `gunicorn -c gunicorn.conf.py`.
- 15:48 prod step 12 (web search): Flask-Limiter 4.1.1 with Redis storage (shared across gunicorn workers). default 60/min; weather 30/min; POST moods 20/min; `/health`+`/ready` exempt. tests cover 429. stopping here.

About 150 min since the venv.

## Open decisions

- Storage: Redis (decided). Mood entries live in Redis. Tests mock Redis.
- One mood per day: overwrite by default (can reject with overwrite=False).
- Docker: Compose with `api` + `redis` (done).
- Endpoints: `GET /health`, `GET /ready`, `GET /weather?city=`, `POST /moods`, `GET /moods`.
