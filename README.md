# 3hr Take-Home Challenge - Weather + Mood API

**Track:** Back End (SPD)
**Stack:** Python + Flask
**Weather API:** OpenWeatherMap
**Submit:** Slack DM to instructor (not Gradescope)
**Time target:** under 3 hours hands-on (planning does not count)

## What this app does

Anonymous users look up weather by city and log a mood for that day. No login.

## How to run

Filled in after the app exists.

### Virtualenv

- Python: 3.13.3
- Path: `.venv/` (local only; ignored)
- Create: `python3 -m venv .venv`
- Activate: `source .venv/bin/activate`
- pip: 26.2.1
- Install: `pip install -r requirements.txt`
- Run: `flask --app wsgi run --host=0.0.0.0 --port=5000`

### Docker

```bash
# needs OPENWEATHER_API_KEY in the environment or in local .env
docker compose up --build --detach
curl http://127.0.0.1:5000/health
docker compose down
```

- API listens on host port **5000** (`0.0.0.0` inside the container)
- Redis is internal only (`redis://redis:6379/0`); not published to the host
- Key is never baked into the image (Compose `environment` / optional `env_file`)
### Environment

- Copy `.env.example` to `.env`
- Set `OPENWEATHER_API_KEY`
- Do not commit `.env`
- Do not bake the key into the image

### Tests

```bash
source .venv/bin/activate
pytest
```

Unit tests live under `tests/unit/`. Weather HTTP and Redis are mocked, so no API key and no Redis needed to run them.

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

Hands-on so far: about 75 min since the venv. next: maybe tighten redis-py timeouts, or a final README polish / clean check from scratch.

## Open decisions

- Storage: Redis (decided). Mood entries live in Redis. Tests mock Redis.
- One mood per day: overwrite by default (can reject with overwrite=False).
- Docker: Compose with `api` + `redis` (done). Instructor needs Docker Desktop or equivalent.
- Endpoints so far: `GET /health`, `GET /weather?city=`, `POST /moods`, `GET /moods`.
- DM format: zip or repo link (ask instructor)
