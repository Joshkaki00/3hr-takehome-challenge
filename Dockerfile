# Pin exact tag (never :latest).
FROM python:3.12.7-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY wsgi.py .
COPY gunicorn.conf.py .

# Non-root runtime (limit blast radius if the app is compromised).
# See Docker / Flask prod guidance: never run the process as root.
RUN groupadd --gid 1000 app \
    && useradd --uid 1000 --gid app --home-dir /app --shell /usr/sbin/nologin app \
    && chown -R app:app /app
USER app

# Key and Redis URL come from env / Compose, never baked in.
EXPOSE 5000

# App-level probe (not just "process running"). No curl in slim: use stdlib.
# https://docs.docker.com/reference/dockerfile/#healthcheck
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5000/ready', timeout=2)"

# Prod WSGI + JSON logs via gunicorn.conf.py
# See: https://flask.palletsprojects.com/en/stable/deploying/gunicorn/
CMD ["gunicorn", "-c", "gunicorn.conf.py", "wsgi:app"]
