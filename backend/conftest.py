import os

# The [tool.pytest.ini_options].env block in pyproject.toml is authoritative for
# these values: pytest-env's hookimpl runs tryfirst=True, so it always sets them
# before this file loads. The setdefault calls below are an inert fallback —
# they can never run before pytest-env has already set the values, and
# setdefault would not overwrite them anyway. Any change to the test
# environment (e.g. switching DATABASE_URL to Postgres) must be made in
# pyproject.toml as well, or it will silently have no effect.
os.environ.setdefault("DJANGO_SECRET_KEY", "test-only-not-a-real-secret")
os.environ.setdefault("DJANGO_DEBUG", "True")
os.environ.setdefault(
    "DATABASE_URL", "postgres://femopedia:femopedia@localhost:5432/femopedia"
)
os.environ.setdefault("NEO4J_PASSWORD", "femopedia-dev-password")
