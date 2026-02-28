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
