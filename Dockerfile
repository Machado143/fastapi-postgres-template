FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000  # default for compatibility, actual port comes from $PORT

# run migrations then start uvicorn on dynamic port provided by host (Railway sets $PORT)
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT}" ]

# healthcheck uses the same variable, falling back to 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1