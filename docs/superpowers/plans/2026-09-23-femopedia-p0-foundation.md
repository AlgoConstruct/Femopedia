# Femopedia P0 — Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stand up the Femopedia monorepo and Django backend so that an anonymous device can obtain a token, authenticate with it, and reach a health endpoint, with Postgres, Redis, Chroma, and Neo4j running under Docker Compose.

**Architecture:** A monorepo with the existing TanStack PWA in `frontend/` and a new Django 5.2 project in `backend/`. Django exposes a DRF API. Anonymous identity is a device token: the client receives a random token once, the server stores only its SHA-256 hash, and a custom DRF authentication class resolves that header to a `Device` row. Four datastores run as Compose services; only Postgres holds anything that cannot be rebuilt.

**Tech Stack:** Python 3.13, Django 5.2 LTS, Django REST Framework, Postgres 16 with pgvector, Redis 7, ChromaDB 1.5.9, Neo4j 5.26 Community, uv, pytest + pytest-django, Docker Compose.

## Global Constraints

- Python pinned to 3.13 — Wagtail 7.0 (arriving in P1.5) supports Python 3.9–3.13 and Django 4.2/5.1/5.2, so neither may drift ahead.
- Django pinned to `>=5.2,<6.0` (LTS) for the same reason.
- No personal identifier is ever required to use the API. A device token is the only credential in P0.
- Only the SHA-256 hash of a device token is persisted. The raw token is returned exactly once, at issuance, and never logged.
- Deletion is a hard cascade from `Device`. No soft-delete flags anywhere.
- Chroma and Neo4j hold derived data only and must remain rebuildable from Postgres.
- Secrets come from environment variables. No secret is committed, including in `.env.example`.
- Every task ends with a commit on branch `design/v1-anonymous-ai-qa`.

---

### Task 1: Monorepo restructure

The git repository currently lives at `Femopedia/frontend/.git`, so `backend/` cannot be tracked. Move the repository up one level. Git detects the moved files as renames and history is preserved.

**Files:**
- Move: `Femopedia/frontend/.git` → `Femopedia/.git`
- Create: `Femopedia/.gitignore`
- Create: `Femopedia/README.md`

**Interfaces:**
- Consumes: nothing
- Produces: a repository rooted at `Femopedia/`, with all previously tracked files now at paths prefixed `frontend/`

- [ ] **Step 1: Back up the repository before touching `.git`**

```bash
cd /Users/aayush/Documents/AlgoConstruct
cp -R Femopedia Femopedia.backup-p0
```

Verify the copy exists and is non-empty:

```bash
ls Femopedia.backup-p0/frontend/.git/HEAD
```

Expected: the path prints. Do not proceed if it does not.

- [ ] **Step 2: Confirm the working tree is clean**

```bash
cd /Users/aayush/Documents/AlgoConstruct/Femopedia/frontend
git status --short
git branch --show-current
```

Expected: no modified tracked files, and branch `design/v1-anonymous-ai-qa`. Untracked files under `docs/` are fine. If tracked files are modified, commit or stash them first.

- [ ] **Step 3: Move the git directory up one level**

```bash
cd /Users/aayush/Documents/AlgoConstruct/Femopedia
mv frontend/.git .git
git status --short | head -20
```

Expected: git now reports the former root files as deleted and their `frontend/`-prefixed counterparts as untracked.

- [ ] **Step 4: Write the root `.gitignore`**

Create `Femopedia/.gitignore`:

```gitignore
.DS_Store
*.pyc
__pycache__/
.venv/
.env
backend/.env
staticfiles/
media/
.pytest_cache/
.ruff_cache/
node_modules/
.superpowers/
```

- [ ] **Step 5: Write the root `README.md`**

Create `Femopedia/README.md`:

```markdown
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
```

- [ ] **Step 6: Stage the move and verify git recorded renames rather than deletions**

```bash
cd /Users/aayush/Documents/AlgoConstruct/Femopedia
git add -A
git status --short | grep -c '^R' 
```

Expected: a number greater than 100 (the frontend source files, detected as renames). If it prints 0, stop — the move did not register and history attribution is at risk.

- [ ] **Step 7: Commit**

```bash
cd /Users/aayush/Documents/AlgoConstruct/Femopedia
git commit -m "chore: move repository root up to monorepo level

Git lived in frontend/, which made a sibling backend/ untrackable.
All previously tracked paths are now prefixed frontend/."
```

- [ ] **Step 8: Move the docs directory to the repository root**

The specs and plans belong to the monorepo, not the frontend.

```bash
cd /Users/aayush/Documents/AlgoConstruct/Femopedia
git mv frontend/docs/superpowers docs/superpowers 2>/dev/null || { mkdir -p docs && git mv frontend/docs/superpowers docs/superpowers; }
git add -A && git commit -m "chore: move superpowers docs to repository root"
ls docs/superpowers/specs docs/superpowers/plans
```

Expected: both directories list their markdown files.

- [ ] **Step 9: Reconfigure the Vercel project for the new root**

The repository root moved, so Vercel is now building the wrong directory. In the Vercel dashboard for this project, under Settings:

1. **General → Root Directory**: set to `frontend`.
2. **Git → Ignored Build Step**: set to

```bash
git diff --quiet HEAD^ HEAD -- frontend/
```

Exit code 0 skips the build, so backend-only commits no longer trigger a frontend deploy.

Verify by pushing a backend-only commit later in this plan and confirming Vercel reports the build as skipped.

---

### Task 2: Django project skeleton with a health endpoint

**Files:**
- Create: `backend/pyproject.toml`
- Create: `backend/.python-version`
- Create: `backend/.env.example`
- Create: `backend/manage.py`
- Create: `backend/config/__init__.py`
- Create: `backend/config/settings.py`
- Create: `backend/config/urls.py`
- Create: `backend/config/wsgi.py`
- Create: `backend/apps/__init__.py`
- Create: `backend/apps/core/__init__.py`
- Create: `backend/apps/core/apps.py`
- Create: `backend/apps/core/views.py`
- Create: `backend/apps/core/urls.py`
- Test: `backend/tests/__init__.py`
- Test: `backend/conftest.py`
- Test: `backend/tests/test_health.py`

**Interfaces:**
- Consumes: the monorepo root from Task 1
- Produces: `GET /api/health/` returning HTTP 200 with JSON body `{"status": "ok"}`; a `config.settings` module reading configuration from environment variables; a pytest suite runnable with `uv run pytest`

- [ ] **Step 1: Create the uv project and pin Python**

```bash
cd /Users/aayush/Documents/AlgoConstruct/Femopedia
mkdir -p backend/apps/core backend/config backend/tests
cd backend
echo "3.13" > .python-version
```

Create `backend/pyproject.toml`:

```toml
[project]
name = "femopedia-backend"
version = "0.1.0"
requires-python = ">=3.13,<3.14"
dependencies = [
    "django>=5.2,<6.0",
    "djangorestframework>=3.15",
    "psycopg[binary]>=3.2",
    "django-environ>=0.11",
    "redis>=5.0",
    "neo4j>=5.26",
    "chromadb>=1.5,<2",
    "httpx>=0.27",
]

[dependency-groups]
dev = [
    "pytest>=8.0",
    "pytest-django>=4.9",
    "factory-boy>=3.3",
    "ruff>=0.6",
]

[tool.pytest.ini_options]
DJANGO_SETTINGS_MODULE = "config.settings"
python_files = ["test_*.py"]
testpaths = ["tests"]
markers = ["integration: requires docker compose services to be running"]

[tool.ruff]
line-length = 100
```

Install:

```bash
cd /Users/aayush/Documents/AlgoConstruct/Femopedia/backend
uv sync
```

Expected: a `.venv` is created and `uv.lock` is written.

- [ ] **Step 2: Write the failing test**

Create `backend/tests/__init__.py` as an empty file, then `backend/tests/test_health.py`:

```python
import pytest
from django.test import Client


@pytest.mark.django_db
def test_health_endpoint_returns_ok():
    client = Client()
    response = client.get("/api/health/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

Create `backend/conftest.py` (at the backend root, not under `tests/` — pytest-django resolves settings from the rootdir conftest before test packages are imported):

```python
import os

os.environ.setdefault("DJANGO_SECRET_KEY", "test-only-not-a-real-secret")
os.environ.setdefault("DJANGO_DEBUG", "True")
os.environ.setdefault("DATABASE_URL", "sqlite:///test-db.sqlite3")
```

Note: SQLite is used for Task 2 only, so the suite runs before Compose exists. Task 3 switches it to Postgres.

- [ ] **Step 3: Run the test to verify it fails**

```bash
cd /Users/aayush/Documents/AlgoConstruct/Femopedia/backend
uv run pytest tests/test_health.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'config'`.

- [ ] **Step 4: Write the settings module**

Create `backend/config/__init__.py` and `backend/apps/__init__.py` as empty files.

Create `backend/config/settings.py`:

```python
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DJANGO_DEBUG=(bool, False),
    DJANGO_ALLOWED_HOSTS=(list, ["localhost", "127.0.0.1"]),
)
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("DJANGO_SECRET_KEY")
DEBUG = env("DJANGO_DEBUG")
ALLOWED_HOSTS = env("DJANGO_ALLOWED_HOSTS")

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django.contrib.staticfiles",
    "rest_framework",
    "apps.core",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {"context_processors": []},
    }
]

DATABASES = {"default": env.db("DATABASE_URL")}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kathmandu"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_PERMISSION_CLASSES": [],
    "UNAUTHENTICATED_USER": None,
}

REDIS_URL = env("REDIS_URL", default="redis://localhost:6379/0")
CHROMA_URL = env("CHROMA_URL", default="http://localhost:8001")
NEO4J_URL = env("NEO4J_URL", default="bolt://localhost:7687")
NEO4J_USER = env("NEO4J_USER", default="neo4j")
NEO4J_PASSWORD = env("NEO4J_PASSWORD", default="")
```

`UNAUTHENTICATED_USER` is set to `None` because Femopedia has no Django users in the request path — an anonymous device, not an `AnonymousUser`, is the subject of a request.

- [ ] **Step 5: Write the URL configuration and the view**

Create `backend/apps/core/__init__.py` as an empty file.

Create `backend/apps/core/apps.py`:

```python
from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = "apps.core"
    label = "core"
```

Create `backend/apps/core/views.py`:

```python
from rest_framework.decorators import api_view
from rest_framework.response import Response


@api_view(["GET"])
def health(request):
    return Response({"status": "ok"})
```

Create `backend/apps/core/urls.py`:

```python
from django.urls import path

from apps.core import views

urlpatterns = [
    path("health/", views.health, name="health"),
]
```

Create `backend/config/urls.py`:

```python
from django.urls import include, path

urlpatterns = [
    path("api/", include("apps.core.urls")),
]
```

Create `backend/config/wsgi.py`:

```python
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

application = get_wsgi_application()
```

Create `backend/manage.py`:

```python
#!/usr/bin/env python
import os
import sys


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
```

- [ ] **Step 6: Run the test to verify it passes**

```bash
cd /Users/aayush/Documents/AlgoConstruct/Femopedia/backend
uv run pytest tests/test_health.py -v
```

Expected: PASS.

- [ ] **Step 7: Write `.env.example` with no real values**

Create `backend/.env.example`:

```dotenv
DJANGO_SECRET_KEY=replace-me-with-a-generated-value
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=postgres://femopedia:femopedia@localhost:5432/femopedia
REDIS_URL=redis://localhost:6379/0
CHROMA_URL=http://localhost:8001
NEO4J_URL=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=replace-me
```

- [ ] **Step 8: Commit**

```bash
cd /Users/aayush/Documents/AlgoConstruct/Femopedia
git add backend/ && git commit -m "feat(backend): Django project skeleton with health endpoint"
```

---

### Task 3: Docker Compose services and Postgres-backed tests

**Files:**
- Create: `docker-compose.yml` (repository root)
- Modify: `backend/conftest.py`
- Test: `backend/tests/test_database.py`

**Interfaces:**
- Consumes: `config.settings` from Task 2
- Produces: running services `postgres` (5432), `redis` (6379), `chroma` (8001), `neo4j` (7687 bolt, 7474 http); the test suite running against Postgres

- [ ] **Step 1: Write the failing test**

Create `backend/tests/test_database.py`:

```python
import pytest
from django.db import connection


@pytest.mark.django_db
def test_database_is_postgres():
    assert connection.vendor == "postgresql"


@pytest.mark.django_db
def test_pgvector_extension_is_available():
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1 FROM pg_available_extensions WHERE name = 'vector'")
        assert cursor.fetchone() is not None
```

- [ ] **Step 2: Run the test to verify it fails**

```bash
cd /Users/aayush/Documents/AlgoConstruct/Femopedia/backend
uv run pytest tests/test_database.py -v
```

Expected: FAIL — `assert 'sqlite' == 'postgresql'`.

- [ ] **Step 3: Write the Compose file**

Create `docker-compose.yml` at the repository root:

```yaml
services:
  postgres:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_USER: femopedia
      POSTGRES_PASSWORD: femopedia
      POSTGRES_DB: femopedia
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U femopedia"]
      interval: 5s
      timeout: 3s
      retries: 10

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 10

  chroma:
    image: chromadb/chroma:1.5.9
    ports:
      - "8001:8000"
    volumes:
      - chromadata:/data
    healthcheck:
      # The chroma image ships no curl, wget, nc or python3. bash is present,
      # so its /dev/tcp pseudo-device is the probe available to us. Exec form,
      # so no outer shell mangles the redirect. This proves the port accepts
      # connections; the HTTP heartbeat is exercised by Task 6's deep health
      # check, which calls /api/v2/heartbeat from Django.
      test: ["CMD", "bash", "-c", ":> /dev/tcp/127.0.0.1/8000"]
      interval: 10s
      timeout: 5s
      retries: 10

  neo4j:
    image: neo4j:5.26-community
    environment:
      NEO4J_AUTH: neo4j/femopedia-dev-password
      NEO4J_PLUGINS: '["apoc"]'
    ports:
      - "7474:7474"
      - "7687:7687"
    volumes:
      - neo4jdata:/data
    healthcheck:
      test: ["CMD-SHELL", "wget -qO- http://localhost:7474 || exit 1"]
      interval: 10s
      timeout: 5s
      retries: 10

volumes:
  pgdata:
  chromadata:
  neo4jdata:
```

- [ ] **Step 4: Start the services and confirm all four are healthy**

```bash
cd /Users/aayush/Documents/AlgoConstruct/Femopedia
docker compose up -d
sleep 30
docker compose ps
```

Expected: four services listed, each `running` and `healthy`.

If the `chromadb/chroma:1.5.9` tag fails to pull, list the available tags and pin the newest stable (non-`.dev`) 1.x tag instead, then re-run:

```bash
docker run --rm quay.io/skopeo/stable list-tags docker://docker.io/chromadb/chroma | tail -30
```

- [ ] **Step 5: Point tests at Postgres**

Task 2 established that pytest-django force-loads Django settings during
`pytest_load_initial_conftests`, before any `conftest.py` is imported, so the
authoritative place for test environment variables is the `env` block in
`backend/pyproject.toml`, supplied by the `pytest-env` plugin. `conftest.py`
is a redundant safety net kept in sync with it.

Replace the `env` list inside `[tool.pytest.ini_options]` in
`backend/pyproject.toml` with:

```toml
env = [
    "DJANGO_SECRET_KEY=test-only-not-a-real-secret",
    "DJANGO_DEBUG=True",
    "DATABASE_URL=postgres://femopedia:femopedia@localhost:5432/femopedia",
    "NEO4J_PASSWORD=femopedia-dev-password",
]
```

Replace `backend/conftest.py` with the matching values:

```python
import os

os.environ.setdefault("DJANGO_SECRET_KEY", "test-only-not-a-real-secret")
os.environ.setdefault("DJANGO_DEBUG", "True")
os.environ.setdefault(
    "DATABASE_URL", "postgres://femopedia:femopedia@localhost:5432/femopedia"
)
os.environ.setdefault("NEO4J_PASSWORD", "femopedia-dev-password")
```

- [ ] **Step 6: Run migrations and the test to verify it passes**

```bash
cd /Users/aayush/Documents/AlgoConstruct/Femopedia/backend
cp .env.example .env
uv run python manage.py migrate
uv run pytest tests/ -v
```

Expected: all tests PASS, including `test_pgvector_extension_is_available`.

Edit `.env` so `NEO4J_PASSWORD=femopedia-dev-password` and `DJANGO_SECRET_KEY` is a generated value:

```bash
uv run python -c "from django.core.management.utils import get_random_secret_key as k; print(k())"
```

- [ ] **Step 7: Commit**

```bash
cd /Users/aayush/Documents/AlgoConstruct/Femopedia
git add docker-compose.yml backend/conftest.py backend/pyproject.toml backend/tests/ && git commit -m "feat: docker compose services, tests run on postgres"
```

---

### Task 4: Device model and token issuance

**Files:**
- Create: `backend/apps/accounts/__init__.py`
- Create: `backend/apps/accounts/apps.py`
- Create: `backend/apps/accounts/models.py`
- Create: `backend/apps/accounts/tokens.py`
- Create: `backend/apps/accounts/views.py`
- Create: `backend/apps/accounts/urls.py`
- Create: `backend/apps/accounts/migrations/__init__.py`
- Modify: `backend/config/settings.py` (add `apps.accounts` to `INSTALLED_APPS`)
- Modify: `backend/config/urls.py` (include the accounts URLs)
- Test: `backend/tests/test_devices.py`

**Interfaces:**
- Consumes: `config.settings`, the DRF setup from Task 2
- Produces:
  - `apps.accounts.models.Device` — fields `id: UUID`, `token_hash: str`, `created_at`, `locale: str`, `last_seen`; property `is_authenticated -> bool` returning `True`
  - `apps.accounts.tokens.generate_device_token() -> str` — 43-character URL-safe token
  - `apps.accounts.tokens.hash_device_token(raw: str) -> str` — 64-character lowercase SHA-256 hex digest
  - `POST /api/devices/` returning HTTP 201 with `{"device_id": str, "device_token": str}`

- [ ] **Step 1: Write the failing test**

Create `backend/tests/test_devices.py`:

```python
import pytest
from django.test import Client

from apps.accounts.models import Device
from apps.accounts.tokens import generate_device_token, hash_device_token


def test_generated_tokens_are_unique_and_long():
    tokens = {generate_device_token() for _ in range(100)}
    assert len(tokens) == 100
    assert all(len(t) >= 43 for t in tokens)


def test_hash_is_stable_sha256_hex():
    digest = hash_device_token("abc")
    assert digest == hash_device_token("abc")
    assert len(digest) == 64
    assert digest == digest.lower()
    assert digest != hash_device_token("abd")


@pytest.mark.django_db
def test_create_device_returns_token_once_and_stores_only_the_hash():
    client = Client()
    response = client.post("/api/devices/")

    assert response.status_code == 201
    body = response.json()
    assert set(body) == {"device_id", "device_token"}

    device = Device.objects.get(id=body["device_id"])
    assert device.token_hash == hash_device_token(body["device_token"])
    assert body["device_token"] not in device.token_hash


@pytest.mark.django_db
def test_device_is_authenticated_property():
    device = Device.objects.create(token_hash=hash_device_token("x"))
    assert device.is_authenticated is True
```

- [ ] **Step 2: Run the test to verify it fails**

```bash
cd /Users/aayush/Documents/AlgoConstruct/Femopedia/backend
uv run pytest tests/test_devices.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'apps.accounts'`.

- [ ] **Step 3: Write the token helpers**

Create `backend/apps/accounts/__init__.py` and `backend/apps/accounts/migrations/__init__.py` as empty files.

Create `backend/apps/accounts/apps.py`:

```python
from django.apps import AppConfig


class AccountsConfig(AppConfig):
    name = "apps.accounts"
    label = "accounts"
```

Create `backend/apps/accounts/tokens.py`:

```python
import hashlib
import secrets


def generate_device_token() -> str:
    """Return a fresh URL-safe device token. Shown to the client exactly once."""
    return secrets.token_urlsafe(32)


def hash_device_token(raw: str) -> str:
    """Return the lowercase SHA-256 hex digest stored in place of the raw token."""
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()
```

- [ ] **Step 4: Write the model**

Create `backend/apps/accounts/models.py`:

```python
import uuid

from django.db import models


class Device(models.Model):
    """An anonymous client. The only credential Femopedia requires."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    token_hash = models.CharField(max_length=64, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    locale = models.CharField(max_length=16, default="ne")
    last_seen = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "accounts_device"

    @property
    def is_authenticated(self) -> bool:
        """DRF permission classes check this attribute on request.user."""
        return True

    def __str__(self) -> str:
        return f"Device {self.id}"
```

- [ ] **Step 5: Write the issuance endpoint**

Create `backend/apps/accounts/views.py`:

```python
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from apps.accounts.models import Device
from apps.accounts.tokens import generate_device_token, hash_device_token


@api_view(["POST"])
def create_device(request):
    """Issue an anonymous device token. The raw token is returned once and never stored."""
    raw_token = generate_device_token()
    device = Device.objects.create(
        token_hash=hash_device_token(raw_token),
        locale=request.data.get("locale", "ne") if request.data else "ne",
    )
    return Response(
        {"device_id": str(device.id), "device_token": raw_token},
        status=status.HTTP_201_CREATED,
    )
```

Create `backend/apps/accounts/urls.py`:

```python
from django.urls import path

from apps.accounts import views

urlpatterns = [
    path("devices/", views.create_device, name="create-device"),
]
```

- [ ] **Step 6: Register the app and the URLs**

In `backend/config/settings.py`, change the `INSTALLED_APPS` entry `"apps.core",` to:

```python
    "apps.core",
    "apps.accounts",
```

Replace `backend/config/urls.py` with:

```python
from django.urls import include, path

urlpatterns = [
    path("api/", include("apps.core.urls")),
    path("api/", include("apps.accounts.urls")),
]
```

- [ ] **Step 7: Generate and apply the migration**

```bash
cd /Users/aayush/Documents/AlgoConstruct/Femopedia/backend
uv run python manage.py makemigrations accounts
uv run python manage.py migrate
```

Expected: `accounts/migrations/0001_initial.py` is created and applied.

- [ ] **Step 8: Run the tests to verify they pass**

```bash
uv run pytest tests/test_devices.py -v
```

Expected: all four tests PASS.

- [ ] **Step 9: Commit**

```bash
cd /Users/aayush/Documents/AlgoConstruct/Femopedia
git add backend/ && git commit -m "feat(accounts): anonymous device model and token issuance"
```

---

### Task 5: Device token authentication

**Files:**
- Create: `backend/apps/accounts/authentication.py`
- Modify: `backend/config/settings.py` (`REST_FRAMEWORK` default authentication classes)
- Modify: `backend/apps/core/views.py` (add an authenticated echo endpoint)
- Modify: `backend/apps/core/urls.py`
- Test: `backend/tests/test_authentication.py`

**Interfaces:**
- Consumes: `apps.accounts.models.Device`, `apps.accounts.tokens.hash_device_token` from Task 4
- Produces:
  - `apps.accounts.authentication.DeviceTokenAuthentication` — a DRF authentication class reading the `X-Device-Token` header and returning `(Device, None)`
  - `GET /api/whoami/` returning HTTP 200 with `{"device_id": str}` when authenticated, HTTP 401 otherwise

- [ ] **Step 1: Write the failing test**

Create `backend/tests/test_authentication.py`:

```python
import pytest
from django.test import Client

from apps.accounts.models import Device
from apps.accounts.tokens import generate_device_token, hash_device_token


@pytest.fixture
def device_with_token(db):
    raw = generate_device_token()
    device = Device.objects.create(token_hash=hash_device_token(raw))
    return device, raw


@pytest.mark.django_db
def test_whoami_returns_the_device_for_a_valid_token(device_with_token):
    device, raw = device_with_token
    response = Client().get("/api/whoami/", headers={"x-device-token": raw})
    assert response.status_code == 200
    assert response.json() == {"device_id": str(device.id)}


@pytest.mark.django_db
def test_whoami_rejects_a_missing_token():
    response = Client().get("/api/whoami/")
    assert response.status_code == 401


@pytest.mark.django_db
def test_whoami_rejects_an_unknown_token():
    response = Client().get("/api/whoami/", headers={"x-device-token": "not-a-real-token"})
    assert response.status_code == 401


@pytest.mark.django_db
def test_authentication_updates_last_seen(device_with_token):
    device, raw = device_with_token
    before = device.last_seen
    Client().get("/api/whoami/", headers={"x-device-token": raw})
    device.refresh_from_db()
    assert device.last_seen > before
```

- [ ] **Step 2: Run the test to verify it fails**

```bash
cd /Users/aayush/Documents/AlgoConstruct/Femopedia/backend
uv run pytest tests/test_authentication.py -v
```

Expected: FAIL — 404 on `/api/whoami/`.

- [ ] **Step 3: Write the authentication class**

Create `backend/apps/accounts/authentication.py`:

```python
from django.utils import timezone
from rest_framework import authentication, exceptions

from apps.accounts.models import Device
from apps.accounts.tokens import hash_device_token

HEADER = "HTTP_X_DEVICE_TOKEN"


class DeviceTokenAuthentication(authentication.BaseAuthentication):
    """Resolve the X-Device-Token header to a Device.

    The raw token never leaves the client after issuance; only its hash is
    compared here, so a database leak does not yield usable credentials.
    """

    def authenticate(self, request):
        raw_token = request.META.get(HEADER)
        if not raw_token:
            return None

        try:
            device = Device.objects.get(token_hash=hash_device_token(raw_token))
        except Device.DoesNotExist:
            raise exceptions.AuthenticationFailed("Unknown device token.")

        Device.objects.filter(pk=device.pk).update(last_seen=timezone.now())
        return (device, None)

    def authenticate_header(self, request):
        return "X-Device-Token"
```

- [ ] **Step 4: Wire it in as the default and add the endpoint**

In `backend/config/settings.py`, replace the `REST_FRAMEWORK` block with:

```python
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "apps.accounts.authentication.DeviceTokenAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "UNAUTHENTICATED_USER": None,
}
```

Append to `backend/apps/core/views.py`:

```python
from rest_framework.permissions import AllowAny


@api_view(["GET"])
def whoami(request):
    return Response({"device_id": str(request.user.id)})
```

and change the existing `health` view so it stays public:

```python
@api_view(["GET"])
@permission_classes([AllowAny])
def health(request):
    return Response({"status": "ok"})
```

adding `permission_classes` to the existing import line so it reads:

```python
from rest_framework.decorators import api_view, permission_classes
```

Put every new import at the top of the file with the existing ones rather than beside the function that uses it. Ruff runs in CI and rejects imports that are not at module level.

Replace `backend/apps/core/urls.py` with:

```python
from django.urls import path

from apps.core import views

urlpatterns = [
    path("health/", views.health, name="health"),
    path("whoami/", views.whoami, name="whoami"),
]
```

In `backend/apps/accounts/views.py`, make issuance public by adding to the imports:

```python
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
```

and decorating `create_device` with `@permission_classes([AllowAny])` directly beneath its `@api_view(["POST"])` line. Without this, no client could ever obtain a first token.

- [ ] **Step 5: Run the tests to verify they pass**

```bash
cd /Users/aayush/Documents/AlgoConstruct/Femopedia/backend
uv run pytest tests/ -v
```

Expected: every test PASSes, including the earlier health and device tests.

- [ ] **Step 6: Commit**

```bash
cd /Users/aayush/Documents/AlgoConstruct/Femopedia
git add backend/ && git commit -m "feat(accounts): device token authentication"
```

---

### Task 6: Deep health check across all four datastores

**Files:**
- Create: `backend/apps/core/checks.py`
- Modify: `backend/apps/core/views.py`
- Modify: `backend/apps/core/urls.py`
- Test: `backend/tests/test_checks.py`

**Interfaces:**
- Consumes: `config.settings` values `REDIS_URL`, `CHROMA_URL`, `NEO4J_URL`, `NEO4J_USER`, `NEO4J_PASSWORD`
- Produces:
  - `apps.core.checks.check_postgres() -> bool`
  - `apps.core.checks.check_redis() -> bool`
  - `apps.core.checks.check_chroma() -> bool`
  - `apps.core.checks.check_neo4j() -> bool`
  - `apps.core.checks.run_all() -> dict[str, bool]` with keys `postgres`, `redis`, `chroma`, `neo4j`
  - `GET /api/health/deep/` returning HTTP 200 when every check is true, HTTP 503 otherwise, body `{"services": {...}}`

Each check returns `False` on any exception rather than raising, so one dead service cannot take down the endpoint that reports which service is dead.

- [ ] **Step 1: Write the failing test**

Create `backend/tests/test_checks.py`:

```python
from unittest import mock

import pytest
from django.test import Client

from apps.core import checks


def test_each_check_returns_false_when_the_backend_raises():
    with mock.patch("apps.core.checks.redis.Redis.from_url", side_effect=OSError("down")):
        assert checks.check_redis() is False

    with mock.patch("apps.core.checks.httpx.get", side_effect=OSError("down")):
        assert checks.check_chroma() is False

    with mock.patch("apps.core.checks.GraphDatabase.driver", side_effect=OSError("down")):
        assert checks.check_neo4j() is False


@pytest.mark.django_db
def test_check_postgres_is_true_against_the_test_database():
    assert checks.check_postgres() is True


@pytest.mark.django_db
def test_deep_health_reports_503_when_any_service_is_down():
    with mock.patch(
        "apps.core.checks.run_all",
        return_value={"postgres": True, "redis": False, "chroma": True, "neo4j": True},
    ):
        response = Client().get("/api/health/deep/")
    assert response.status_code == 503
    assert response.json()["services"]["redis"] is False


@pytest.mark.django_db
def test_deep_health_reports_200_when_everything_is_up():
    with mock.patch(
        "apps.core.checks.run_all",
        return_value={"postgres": True, "redis": True, "chroma": True, "neo4j": True},
    ):
        response = Client().get("/api/health/deep/")
    assert response.status_code == 200


@pytest.mark.integration
@pytest.mark.django_db
def test_all_services_are_reachable_under_docker_compose():
    assert checks.run_all() == {
        "postgres": True,
        "redis": True,
        "chroma": True,
        "neo4j": True,
    }
```

- [ ] **Step 2: Run the test to verify it fails**

```bash
cd /Users/aayush/Documents/AlgoConstruct/Femopedia/backend
uv run pytest tests/test_checks.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'apps.core.checks'`.

- [ ] **Step 3: Write the checks module**

Create `backend/apps/core/checks.py`:

```python
import httpx
import redis
from django.conf import settings
from django.db import connection
from neo4j import GraphDatabase


def check_postgres() -> bool:
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            return cursor.fetchone() == (1,)
    except Exception:
        return False


def check_redis() -> bool:
    try:
        client = redis.Redis.from_url(settings.REDIS_URL, socket_connect_timeout=2)
        return bool(client.ping())
    except Exception:
        return False


def check_chroma() -> bool:
    try:
        response = httpx.get(f"{settings.CHROMA_URL}/api/v2/heartbeat", timeout=2.0)
        return response.status_code == 200
    except Exception:
        return False


def check_neo4j() -> bool:
    try:
        driver = GraphDatabase.driver(
            settings.NEO4J_URL,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
            connection_timeout=2,
        )
        driver.verify_connectivity()
        driver.close()
        return True
    except Exception:
        return False


def run_all() -> dict[str, bool]:
    return {
        "postgres": check_postgres(),
        "redis": check_redis(),
        "chroma": check_chroma(),
        "neo4j": check_neo4j(),
    }
```

- [ ] **Step 4: Add the endpoint**

Add `from rest_framework import status` and `from apps.core import checks` to the imports at the top of `backend/apps/core/views.py`, then append the view:

```python
@api_view(["GET"])
@permission_classes([AllowAny])
def health_deep(request):
    services = checks.run_all()
    code = status.HTTP_200_OK if all(services.values()) else status.HTTP_503_SERVICE_UNAVAILABLE
    return Response({"services": services}, status=code)
```

Add to `backend/apps/core/urls.py` inside `urlpatterns`:

```python
    path("health/deep/", views.health_deep, name="health-deep"),
```

- [ ] **Step 5: Run the unit tests to verify they pass**

```bash
cd /Users/aayush/Documents/AlgoConstruct/Femopedia/backend
uv run pytest tests/test_checks.py -v -m "not integration"
```

Expected: PASS.

- [ ] **Step 6: Run the integration test against live Compose services**

```bash
cd /Users/aayush/Documents/AlgoConstruct/Femopedia
docker compose ps
cd backend && uv run pytest tests/test_checks.py -v -m integration
```

Expected: PASS. A failure here names the unreachable service — fix Compose or `.env` before continuing.

- [ ] **Step 7: Commit**

```bash
cd /Users/aayush/Documents/AlgoConstruct/Femopedia
git add backend/ && git commit -m "feat(core): deep health check across postgres, redis, chroma, neo4j"
```

---

### Task 7: Continuous integration

CI exists from P0 because P2 makes crisis recall a release gate. The pipeline has to be in place before the tests that matter arrive.

**Files:**
- Create: `.github/workflows/backend.yml`
- Create: `backend/Dockerfile`

**Interfaces:**
- Consumes: the pytest suite and `pyproject.toml` from Tasks 2–6
- Produces: a GitHub Actions workflow running `uv run pytest -m "not integration"` against a real Postgres service on every push and pull request

- [ ] **Step 1: Write the Dockerfile**

Create `backend/Dockerfile`:

```dockerfile
FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY . .

CMD ["uv", "run", "gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
```

Add `"gunicorn>=22.0",` to the `dependencies` list in `backend/pyproject.toml`, then:

```bash
cd /Users/aayush/Documents/AlgoConstruct/Femopedia/backend && uv sync
```

- [ ] **Step 2: Write the workflow**

Create `.github/workflows/backend.yml`:

```yaml
name: backend

on:
  push:
    branches: ["**"]
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: backend

    services:
      postgres:
        image: pgvector/pgvector:pg16
        env:
          POSTGRES_USER: femopedia
          POSTGRES_PASSWORD: femopedia
          POSTGRES_DB: femopedia
        ports: ["5432:5432"]
        options: >-
          --health-cmd "pg_isready -U femopedia"
          --health-interval 5s
          --health-timeout 3s
          --health-retries 10

    env:
      DJANGO_SECRET_KEY: ci-only-not-a-real-secret
      DJANGO_DEBUG: "True"
      DATABASE_URL: postgres://femopedia:femopedia@localhost:5432/femopedia
      NEO4J_PASSWORD: ci-placeholder

    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
        with:
          enable-cache: true
      - run: uv sync --frozen
      - run: uv run ruff check .
      - run: uv run pytest -v -m "not integration"
```

- [ ] **Step 3: Verify the workflow's commands pass locally first**

```bash
cd /Users/aayush/Documents/AlgoConstruct/Femopedia/backend
uv run ruff check .
uv run pytest -v -m "not integration"
```

Expected: ruff reports no errors and every non-integration test passes. Fix anything ruff flags before pushing — a red first CI run teaches nothing.

- [ ] **Step 4: Commit and push, then confirm CI is green**

```bash
cd /Users/aayush/Documents/AlgoConstruct/Femopedia
git add .github/ backend/ && git commit -m "ci: run backend test suite on push and pull request"
git push -u origin design/v1-anonymous-ai-qa
gh run watch
```

Expected: the workflow completes successfully. A failure here is a real failure — do not merge past it.

---

## Definition of done for P0

- `docker compose up -d` brings four healthy services up.
- `uv run pytest -v` passes locally, integration tests included.
- `POST /api/devices/` issues a token; `GET /api/whoami/` accepts it and rejects anything else.
- `GET /api/health/deep/` reports each datastore individually and returns 503 when any is down.
- CI is green on `design/v1-anonymous-ai-qa`.
- The repository root is `Femopedia/`, with `frontend/`, `backend/`, and `docs/` as siblings.
- Vercel builds from Root Directory `frontend` and skips backend-only commits.

## What P0 deliberately does not do

No chat, no Jev, no OpenAI, no retrieval, no Wagtail, no encryption of message bodies (there are no messages yet), and no deletion endpoint (added in P5 alongside the settings screen that calls it). Those belong to later plans and adding them here would break the one-deliverable-per-phase rule the spec sets.
