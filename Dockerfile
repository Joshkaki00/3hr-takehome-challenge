# Pin exact tag (never :latest).
FROM python:3.12.7-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY wsgi.py .

# Key and Redis URL come from env / Compose, never baked in.
EXPOSE 5000

# Prod WSGI (not flask run). Exec-form CMD => gunicorn is PID 1 (SIGTERM).
# See: https://flask.palletsprojects.com/en/stable/deploying/gunicorn/
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:5000", "--access-logfile", "-", "--error-logfile", "-", "wsgi:app"]
