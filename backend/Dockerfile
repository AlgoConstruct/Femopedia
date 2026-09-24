FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:0.12.1 /uv /usr/local/bin/uv

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY . .

# Non-root: the image only ever runs gunicorn, and /app is owned by this
# user so the venv it just synced above stays readable.
RUN groupadd --system femopedia && useradd --system --gid femopedia --home-dir /app femopedia \
    && chown -R femopedia:femopedia /app
USER femopedia

# The venv binary is invoked directly rather than via `uv run`: `uv run`
# re-syncs the environment on every container start, which would either
# reinstall the dev dependency group into a production image (uv.lock has
# no separate "frozen" record of the --no-dev choice baked into the image)
# or fail outright with no network access or a read-only filesystem.
CMD ["/app/.venv/bin/gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
