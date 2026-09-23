# Femopedia

Anonymous, language-matched AI health companion for women in Nepal and South Asia.

## Layout

- `frontend/` — TanStack Start PWA
- `backend/` — Django API, content platform, AI pipeline
- `docs/superpowers/specs/` — design specs
- `docs/superpowers/plans/` — implementation plans

## Running locally

    docker compose up -d
    cd backend && uv run python manage.py migrate
    cd backend && uv run python manage.py runserver

See `docs/superpowers/specs/` for the design this implements.
