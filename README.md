# fastapi-postgres-template

Production-ready FastAPI template with PostgreSQL, async SQLAlchemy 2.0,
JWT auth (access + refresh tokens), Docker, Alembic migrations and clean
layered architecture.

[![CI](https://github.com/Machado143/fastapi-postgres-template/actions/workflows/ci.yml/badge.svg)](https://github.com/Machado143/fastapi-postgres-template/actions/workflows/ci.yml)

---

## Stack

| Layer | Technology |
|---|---|
| Framework | FastAPI 0.115 |
| ORM | SQLAlchemy 2.0 async (`asyncpg`) |
| Migrations | Alembic |
| Auth | JWT via `python-jose` + `bcrypt` |
| Validation | Pydantic v2 |
| Rate limiting | slowapi |
| Metrics | prometheus-client |
| Logging | python-json-logger (structured JSON) |
| Tests | pytest + pytest-asyncio + httpx |
| Container | Docker + docker-compose |
| Deploy | Railway |

---

## Architecture

```
app/
├── api/
│   ├── dependencies.py       # get_current_user (auth guard)
│   └── v1/
│       ├── router.py         # mounts auth + users routers
│       └── routers/
│           ├── auth.py       # POST /token, POST /refresh
│           └── users.py      # CRUD endpoints
├── core/
│   ├── config.py             # pydantic-settings (env vars)
│   ├── exceptions.py         # typed HTTP exceptions
│   ├── limiter.py            # slowapi limiter singleton
│   ├── logging.py            # JSON logger + request_id/user_id ctx vars
│   └── security.py           # bcrypt hash/verify + JWT encode/decode
├── db/
│   ├── base.py               # SQLAlchemy declarative Base
│   ├── session.py            # engine (pool) + get_db dependency
│   └── init_db.py
├── models/                   # SQLAlchemy ORM models
├── repositories/             # data access layer (no business logic)
├── schemas/                  # Pydantic request/response schemas
└── services/                 # business logic layer
```

**Design decisions:**
- Business logic lives exclusively in `services/`, never in routers.
- Repositories abstract all ORM calls — services never import SQLAlchemy.
- `get_db` opens a single transaction per request; services use
  `begin_nested()` (SAVEPOINT) for write isolation.
- Connection pool (`pool_size=10, max_overflow=20, pool_pre_ping=True`)
  configured only for PostgreSQL; NullPool used for SQLite in tests.

---

## Quick start (local with Docker)

```bash
git clone https://github.com/Machado143/fastapi-postgres-template
cd fastapi-postgres-template
cp .env.example .env        # edit SECRET_KEY and DATABASE_URL
docker compose up --build
```

API docs: http://localhost:8000/docs

---

## Environment variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `DATABASE_URL` | ✅ | — | PostgreSQL URL (`postgresql+asyncpg://...`) |
| `SECRET_KEY` | ✅ | — | JWT signing secret (min 32 chars recommended) |
| `ALGORITHM` | | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | | `30` | Access token TTL |
| `REFRESH_TOKEN_EXPIRE_DAYS` | | `7` | Refresh token TTL |
| `ENV` | | `dev` | `dev` / `staging` / `production` |
| `DEBUG` | | `false` | Force-disabled in `production` |
| `DB_CONNECT_TIMEOUT` | | `5` | DB connection timeout (seconds) |

---

## Auth flow

```
POST /api/v1/users              → create account
POST /api/v1/auth/token         → { access_token, refresh_token }
GET  /api/v1/users/me           → Authorization: Bearer <access_token>
POST /api/v1/auth/refresh       → { refresh_token } → new token pair
```

Refresh tokens are **rotated on every use** — the old one is deleted
atomically before the new one is created (SAVEPOINT).

---

## CI/CD

GitHub Actions (`.github/workflows/ci.yml`) runs on every push/PR to `main`:

1. **lint** — `ruff check`
2. **test** — `pytest` with SQLite in-memory
3. **build** — `docker build` (validates the image builds cleanly)

Railway deploys automatically on push to `main`. Alembic migrations run
as part of the container startup command:

```
alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

---

## Observability

- **Structured JSON logs** — every record includes `request_id` and
  `user_id` (set after auth) via `contextvars`.
- **Prometheus metrics** — `GET /metrics` exposes `http_request_duration_seconds`
  histogram (method / path / status_code labels).
- **Health check** — `GET /health` pings the database with `SELECT 1`
  and returns `{"status": "ok", "database": "ok"}` or `"degraded"`.

---

## Security

- Passwords hashed with `bcrypt` (cost factor 12), max 72 bytes enforced
  at schema validation level before reaching the hash function.
- Access tokens expire in 30 min (configurable).
- Refresh tokens are single-use and stored hashed in the DB.
- Rate limit on auth endpoints: 5 requests/minute per IP (slowapi).
- Security headers on every response: `HSTS`, `X-Frame-Options`,
  `X-Content-Type-Options`, `Referrer-Policy`.
- CORS configured — tighten `allow_origins` in production.

---

## Trade-offs

| Decision | Why | Alternative |
|---|---|---|
| `begin_nested()` in services | Allows partial rollback without killing the outer transaction; works in tests with rollback isolation | Manage commit explicitly in routers |
| SQLite for tests | Zero infra, fast, portable | `pytest-postgresql` for full PostgreSQL parity |
| `python-jose` for JWT | Widely used, simple API | `authlib` (more features, heavier) |
| bcrypt direct (no passlib) | passlib 1.7.4 is incompatible with bcrypt ≥ 4.x | Pin passlib + bcrypt 3.x |
| NullPool for SQLite | SQLite doesn't support pooling | Use StaticPool |


## CI/CD

A GitHub Actions pipeline verifica o código em cada push/PR para `main`.

- **lint**: roda `ruff` (pode trocar por `flake8` se preferir);
- **test**: instala dependências e executa `pytest`;
- **build**: constrói uma imagem Docker, pronta para push opcional.

O workflow está em `.github/workflows/ci.yml` e só executa as etapas
acima. Para empurrar o artefato para um registry publique a imagem no
`build` job ou adicione um passo `docker push` com `registry`/`username`.

## Observability

The template includes basic infrastructure for monitoring and tracing:

* **Structured JSON logs** – configured with `python-json-logger` and a
  `request_id` filter supplied by middleware; every log record includes a
  UUID that is echoed back in `X-Request-ID` response header.
* **Request‑ID middleware** – `RequestIdMiddleware` sets a context var per
  request and adds the header.
* **Prometheus metrics** – `MetricsMiddleware` measures request latency and
  exposes `/metrics` using `prometheus-client`; a `REQUEST_LATENCY`
  histogram is registered automatically.
* **CORS** – `CORSMiddleware` is enabled; adjust `allow_origins` in
  production.
* **Security headers** – `SecurityHeadersMiddleware` injects common
  protective headers (HSTS, X‑Frame‑Options, etc.).

These pieces raise the project to a much higher observability level and
make it production‑ready for simple deployments.

## Hardening

A few important hardening knobs are included or easy to add:

* **Rate limiting** – the dependency `slowapi` is installed; you can
  decorate routers with `@limiter.limit("5/minute")` or add a global
  middleware once you configure Redis or another store.
* **CORS configuration** – currently wide‑open (`*`), change for your
  domain or use the `settings` object.
* **Database timeouts** – the engine is created with
  `connect_args={'timeout': settings.DB_CONNECT_TIMEOUT}` (defaults to 5s).
* **Security headers** – see above.
* **Timeouts on external calls** – add `httpx` timeouts or circuit breakers
  when integrating external APIs.

These measures are lightweight but significantly raise the bar for a real
SaaS deployment.
