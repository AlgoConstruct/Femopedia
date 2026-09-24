import os

import pytest
from django.core.cache import cache

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
os.environ.setdefault("IDENTIFIER_PEPPER", "test-only-pepper-not-a-real-secret")
os.environ.setdefault("FIELD_ENCRYPTION_KEY", "ZmVtb3BlZGlhLXRlc3Qta2V5LW5vdC1hLXNlY3JldCE=")


@pytest.fixture(autouse=True)
def _clear_throttle_cache():
    """Reset DRF's throttle state between tests.

    DRF's throttle classes always bind to the "default" cache alias (this
    DRF version has no configurable DEFAULT_THROTTLE_CACHE setting), and
    that alias is now backed by the real, shared Redis instance rather than
    an in-process cache. Without this, request counts from one test would
    carry into the next and throttling tests would flake depending on run
    order.
    """
    cache.clear()
    yield
    cache.clear()
