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

CMD ["flask", "--app", "wsgi", "run", "--host=0.0.0.0", "--port=5000"]
