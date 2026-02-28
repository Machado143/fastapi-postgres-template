# fastapi-postgres-template
Production-ready FastAPI template with PostgreSQL, async SQLAlchemy 2.0, JWT auth, Docker, Alembic and clean architecture.

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
