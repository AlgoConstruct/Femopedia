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

    uv run python manage.py migrate
    uv run python manage.py runserver

See `docs/superpowers/specs/` for the design this implements.
