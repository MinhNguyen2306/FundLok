FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORT=8080

RUN chmod +x /app/docker/entrypoint.sh

# Runs `alembic upgrade head` then starts uvicorn (see docker/entrypoint.sh).
CMD ["/app/docker/entrypoint.sh"]
