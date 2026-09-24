# Femopedia

Anonymous, language-matched AI health companion for women in Nepal and South Asia.

## Layout

- `frontend/` — TanStack Start PWA
- `backend/` — Django API, content platform, AI pipeline
- `docs/superpowers/specs/` — design specs
- `docs/superpowers/plans/` — implementation plans

## Running locally

    cp .env.example .env
    docker compose up -d

    cd backend
    cp .env.example .env
    uv run python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
    # paste the generated value into backend/.env as DJANGO_SECRET_KEY

    uv run python -c "import secrets; print(secrets.token_urlsafe(32))"
    # paste the generated value into backend/.env as IDENTIFIER_PEPPER

    uv run python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    # paste the generated value into backend/.env as FIELD_ENCRYPTION_KEY

    uv run python manage.py migrate
    uv run python manage.py runserver

`IDENTIFIER_PEPPER` and `FIELD_ENCRYPTION_KEY` protect stored email/username
identifiers (see `backend/apps/accounts/crypto.py`); an empty value for either
now fails startup rather than silently degrading protection (see
`backend/apps/core/checks.py`).

See `docs/superpowers/specs/` for the design this implements.

## API schema

The OpenAPI 3 schema lives at `backend/schema.yml` and is generated from the
code, not written by hand. Regenerate it whenever an endpoint or its request or
response shape changes:

    cd backend && uv run python manage.py spectacular \
        --file schema.yml --validate --fail-on-warn

A stale `schema.yml` fails the test suite, because the frontend generates its
request and response types from that file and a drifted copy produces wrong
types silently.

Browsable docs are served at `/api/docs/` (Swagger UI) and `/api/redoc/`, with
the raw schema at `/api/schema/`. They are not public: a schema enumerates the
whole API surface, so access requires `DEBUG`, or a matching `X-Docs-Token`
header when `DOCS_TOKEN` is set in the environment. With `DOCS_TOKEN` unset and
`DEBUG` off, the schema is served to nobody.
