# Femopedia Accounts — Core Implementation Plan (A of 2)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A woman can create an account three ways short of OAuth, sign in on a second device, see which devices are signed in, revoke one, export everything held about her, and delete it all — while anonymous use continues to work exactly as before.

**Architecture:** The device token stays the only credential. Signing in binds `Device.account`; signing out unbinds, deletes the device row and issues a fresh anonymous token. Anonymous and signed-in are one object in two states, so every endpoint built in P0 keeps working untouched. Identifiers (email, username) are stored as an HMAC blind index for lookup plus a Fernet-encrypted value, so a database dump yields neither addresses nor a usable index.

**Tech Stack:** Python 3.13, Django 5.2, DRF, Postgres 16, `cryptography` (Fernet), Django's password hashers and `django.core.signing`.

## Global Constraints

- Python pinned to 3.13; Django `>=5.2,<6.0`. Wagtail arrives in a later phase and supports Django 5.2; neither may drift ahead.
- **No personal identifier is required to use the API.** Anonymous mode must remain fully functional with no account. Identifiers that are volunteered are blind-indexed, encrypted, exportable and deletable.
- Only the SHA-256 hash of a device token is persisted; the raw token is returned exactly once and never logged.
- Deletion is a hard cascade. No soft-delete flags anywhere, and no grace period.
- Secrets come from environment variables. Nothing secret is committed, including in `.env.example`.
- New dependencies carry an upper version bound, per the drift lesson from P0.
- Ruff must exit 0; every task ends with a commit on the working branch.

## Deferred from the spec, deliberately

- **History merge at signup.** The spec's `bring_history` decision and `GET /api/devices/history-summary/` operate on `Conversation` and `Message`, which do not exist — P0 deferred chat. Building the flow now would mean a count that is always zero and a delete that deletes nothing. It belongs to the phase that adds conversations, and that phase must implement it before any conversation is ever written.
- **Google OAuth and identifier management** (`POST/DELETE /api/account/identifiers/`) — plan B.

---

### Task 1: Crypto helpers for identifier storage

**Files:**
- Create: `backend/apps/accounts/crypto.py`
- Modify: `backend/config/settings.py`
- Modify: `backend/pyproject.toml`
- Modify: `backend/conftest.py`
- Modify: `backend/.env.example`
- Test: `backend/tests/test_crypto.py`

**Interfaces:**
- Consumes: nothing
- Produces:
  - `apps.accounts.crypto.blind_index(value: str) -> str` — 64-char lowercase hex HMAC-SHA256 of the normalised value
  - `apps.accounts.crypto.encrypt(value: str) -> str` — Fernet token as `str`
  - `apps.accounts.crypto.decrypt(token: str) -> str`
  - `settings.IDENTIFIER_PEPPER`, `settings.FIELD_ENCRYPTION_KEY`

- [ ] **Step 1: Add the dependency**

```bash
cd /Users/aayush/Documents/AlgoConstruct/Femopedia/backend
```

Add to the `dependencies` list in `backend/pyproject.toml`, after `drf-spectacular`:

```toml
    "cryptography>=43,<47",
```

Then run `uv sync` and note the resolved version. If it resolves outside the range, stop and report rather than widening the bound.

- [ ] **Step 2: Write the failing test**

Create `backend/tests/test_crypto.py`:

```python
import pytest
from django.test import override_settings

from apps.accounts import crypto


def test_blind_index_is_stable_and_64_hex_chars():
    digest = crypto.blind_index("her@example.com")
    assert digest == crypto.blind_index("her@example.com")
    assert len(digest) == 64
    assert digest == digest.lower()
    int(digest, 16)  # raises if not hex


def test_blind_index_normalises_case_and_surrounding_whitespace():
    assert crypto.blind_index("  HER@Example.COM ") == crypto.blind_index("her@example.com")


def test_blind_index_differs_for_different_values():
    assert crypto.blind_index("a@example.com") != crypto.blind_index("b@example.com")


def test_blind_index_depends_on_the_pepper():
    baseline = crypto.blind_index("her@example.com")
    with override_settings(IDENTIFIER_PEPPER="a-different-pepper"):
        assert crypto.blind_index("her@example.com") != baseline


def test_encrypt_round_trips_and_hides_the_plaintext():
    ciphertext = crypto.encrypt("her@example.com")
    assert "her@example.com" not in ciphertext
    assert crypto.decrypt(ciphertext) == "her@example.com"


def test_encrypting_twice_gives_different_ciphertext():
    # Fernet includes a random IV, so identical plaintexts must not produce
    # identical ciphertexts — otherwise the column leaks which rows match.
    assert crypto.encrypt("her@example.com") != crypto.encrypt("her@example.com")


def test_decrypt_rejects_a_tampered_token():
    from cryptography.fernet import InvalidToken

    ciphertext = crypto.encrypt("her@example.com")
    tampered = ciphertext[:-2] + ("AA" if not ciphertext.endswith("AA") else "BB")
    with pytest.raises(InvalidToken):
        crypto.decrypt(tampered)
```

- [ ] **Step 3: Run the test to verify it fails**

Run: `uv run pytest tests/test_crypto.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'apps.accounts.crypto'`

- [ ] **Step 4: Add the settings**

Append to `backend/config/settings.py`:

```python
# Keyed separately from SECRET_KEY so that rotating a Django session secret
# does not silently destroy the ability to find or read stored identifiers.
# IDENTIFIER_PEPPER keys the blind index used for lookup; FIELD_ENCRYPTION_KEY
# encrypts the identifier values themselves. Losing either is unrecoverable,
# so both must be backed up somewhere other than the database they protect.
IDENTIFIER_PEPPER = env("IDENTIFIER_PEPPER")
FIELD_ENCRYPTION_KEY = env("FIELD_ENCRYPTION_KEY")
```

Neither carries a default. A missing value must stop the process at startup rather than silently produce indexes nobody can reproduce.

- [ ] **Step 5: Write the module**

Create `backend/apps/accounts/crypto.py`:

```python
import hmac
from hashlib import sha256

from cryptography.fernet import Fernet
from django.conf import settings


def _normalise(value: str) -> str:
    """Case- and whitespace-insensitive, so one address has one index."""
    return value.strip().lower()


def blind_index(value: str) -> str:
    """Return the lookup key for an identifier.

    An HMAC rather than a bare hash: the pepper lives in the environment, so
    a database dump alone cannot be brute-forced back into a list of the
    addresses of women who use this application.
    """
    return hmac.new(
        settings.IDENTIFIER_PEPPER.encode("utf-8"),
        _normalise(value).encode("utf-8"),
        sha256,
    ).hexdigest()


def encrypt(value: str) -> str:
    return Fernet(settings.FIELD_ENCRYPTION_KEY.encode("utf-8")).encrypt(
        value.encode("utf-8")
    ).decode("utf-8")


def decrypt(token: str) -> str:
    return Fernet(settings.FIELD_ENCRYPTION_KEY.encode("utf-8")).decrypt(
        token.encode("utf-8")
    ).decode("utf-8")
```

- [ ] **Step 6: Supply test values for the new settings**

Both the authoritative pytest env block and its inert fallback must change together — see the comment at the top of `backend/conftest.py`.

In `backend/pyproject.toml`, add to the `env` list under `[tool.pytest.ini_options]`:

```toml
    "D:IDENTIFIER_PEPPER=test-only-pepper-not-a-real-secret",
    "D:FIELD_ENCRYPTION_KEY=ZmVtb3BlZGlhLXRlc3Qta2V5LW5vdC1hLXNlY3JldCE=",
```

In `backend/conftest.py`, add the matching `os.environ.setdefault` calls with the same two values.

That key is a valid Fernet key (32 url-safe base64-encoded bytes) whose
plaintext reads `femopedia-test-key-not-a-secret!`, so nobody mistakes it for
a real one. It is a test value and is not a secret.

- [ ] **Step 7: Add the variables to `.env.example`**

Append to `backend/.env.example`:

```dotenv
# Generate with:
#   python -c "import secrets; print(secrets.token_urlsafe(32))"
IDENTIFIER_PEPPER=
# Generate with:
#   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
FIELD_ENCRYPTION_KEY=
```

Then set real generated values in your own `backend/.env`, which is git-ignored.

- [ ] **Step 8: Run the tests to verify they pass**

Run: `uv run pytest tests/test_crypto.py -v` — expect all 7 to pass.
Run: `uv run pytest -q` — expect every earlier test still passing.
Run: `uv run ruff check .` — expect exit 0.

- [ ] **Step 9: Commit**

```bash
git add backend/ && git commit -m "feat(accounts): blind index and field encryption helpers"
```

---

### Task 2: Account and Identifier models, and the device binding

**Files:**
- Modify: `backend/apps/accounts/models.py`
- Create: `backend/apps/accounts/migrations/0003_account_identifier.py` (generated)
- Test: `backend/tests/test_account_models.py`

**Interfaces:**
- Consumes: `apps.accounts.crypto.blind_index`, `encrypt`, `decrypt`
- Produces:
  - `apps.accounts.models.Account` — `id: UUID`, `password: str`, `recovery_code_hash: str`, `recovery_code_used_at`, `created_at`; methods `set_password(raw: str) -> None`, `check_password(raw: str) -> bool`, `has_usable_login() -> bool`
  - `apps.accounts.models.Identifier` — `account`, `kind`, `value_hash`, `value_encrypted`, `verified_at`, `created_at`; property `value -> str`; classmethods `create_for(account, kind, value, verified=False) -> Identifier` and `lookup(kind, value) -> Identifier | None`
  - `Account.has_usable_login()` is defined and tested here but consumed by plan B, where removing an identifier must be refused if it would leave no way back in. It is not called elsewhere in this plan.
  - `Identifier.KIND_EMAIL`, `KIND_USERNAME`, `KIND_GOOGLE`
  - `Device.account` (nullable FK, `related_name="devices"`), `Device.bound_at`, `Device.label`

- [ ] **Step 1: Write the failing test**

Create `backend/tests/test_account_models.py`:

```python
import pytest

from apps.accounts.models import Account, Device, Identifier
from apps.accounts.tokens import generate_device_token, hash_device_token


@pytest.mark.django_db
def test_password_is_hashed_not_stored():
    account = Account.objects.create()
    account.set_password("a-real-password")
    account.save()

    account.refresh_from_db()
    assert account.password != "a-real-password"
    assert account.check_password("a-real-password") is True
    assert account.check_password("wrong") is False


@pytest.mark.django_db
def test_an_account_with_no_password_and_no_recovery_code_has_no_usable_login():
    account = Account.objects.create()
    assert account.has_usable_login() is False

    account.set_password("a-real-password")
    assert account.has_usable_login() is True


@pytest.mark.django_db
def test_identifier_stores_no_plaintext_and_round_trips():
    account = Account.objects.create()
    identifier = Identifier.create_for(account, Identifier.KIND_EMAIL, "Her@Example.com")

    assert "Her@Example.com" not in identifier.value_encrypted
    assert "her@example.com" not in identifier.value_encrypted
    assert identifier.value == "Her@Example.com"
    assert len(identifier.value_hash) == 64


@pytest.mark.django_db
def test_identifier_lookup_is_case_insensitive():
    account = Account.objects.create()
    Identifier.create_for(account, Identifier.KIND_EMAIL, "her@example.com")

    assert Identifier.lookup(Identifier.KIND_EMAIL, "HER@EXAMPLE.COM").account_id == account.id
    assert Identifier.lookup(Identifier.KIND_EMAIL, "other@example.com") is None


@pytest.mark.django_db
def test_the_same_identifier_cannot_belong_to_two_accounts():
    from django.db import IntegrityError

    first = Account.objects.create()
    second = Account.objects.create()
    Identifier.create_for(first, Identifier.KIND_EMAIL, "her@example.com")

    with pytest.raises(IntegrityError):
        Identifier.create_for(second, Identifier.KIND_EMAIL, "her@example.com")


@pytest.mark.django_db
def test_the_same_value_may_exist_under_different_kinds():
    account = Account.objects.create()
    Identifier.create_for(account, Identifier.KIND_EMAIL, "sameword")
    Identifier.create_for(account, Identifier.KIND_USERNAME, "sameword")
    assert account.identifiers.count() == 2


@pytest.mark.django_db
def test_a_device_is_anonymous_until_bound():
    device = Device.objects.create(token_hash=hash_device_token(generate_device_token()))
    assert device.account_id is None

    account = Account.objects.create()
    device.account = account
    device.save()

    assert account.devices.get().id == device.id


@pytest.mark.django_db
def test_deleting_an_account_deletes_its_devices_and_identifiers():
    account = Account.objects.create()
    Identifier.create_for(account, Identifier.KIND_EMAIL, "her@example.com")
    Device.objects.create(
        token_hash=hash_device_token(generate_device_token()), account=account
    )

    account.delete()

    assert Device.objects.count() == 0
    assert Identifier.objects.count() == 0
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest tests/test_account_models.py -v`
Expected: FAIL — `ImportError: cannot import name 'Account' from 'apps.accounts.models'`

- [ ] **Step 3: Write the models**

In `backend/apps/accounts/models.py`, add these imports at the top with the existing ones:

```python
from django.contrib.auth.hashers import check_password as django_check_password
from django.contrib.auth.hashers import make_password
from django.utils import timezone

from apps.accounts import crypto
```

Then add, above the existing `Device` class:

```python
class Account(models.Model):
    """A woman's account.

    Deliberately NOT django.contrib.auth.User. Wagtail needs auth.User for
    staff — editors, the clinician, the Nepali reviewer — and putting women's
    accounts in that same table would mean one admin listing or one permission
    mistake exposes them. The password hashers are reused; the model is not.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    password = models.CharField(max_length=128, blank=True, default="")
    recovery_code_hash = models.CharField(max_length=64, blank=True, default="")
    recovery_code_used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "accounts_account"

    def set_password(self, raw: str) -> None:
        self.password = make_password(raw)

    def check_password(self, raw: str) -> bool:
        if not self.password:
            return False
        return django_check_password(raw, self.password)

    def has_usable_login(self) -> bool:
        """True when at least one way back in exists.

        Used to refuse removing the last credential, which would be a lockout
        rather than a preference.
        """
        return bool(self.password) or bool(self.recovery_code_hash)

    def __str__(self) -> str:
        return f"Account {self.id}"


class Identifier(models.Model):
    """One verified way into an account.

    The value is stored twice: a peppered HMAC for lookup, and a Fernet
    ciphertext for display and delivery. A dump of this table yields neither
    a list of addresses nor an index anyone can reproduce without the pepper.
    """

    KIND_EMAIL = "email"
    KIND_USERNAME = "username"
    KIND_GOOGLE = "google"
    KINDS = [
        (KIND_EMAIL, "Email"),
        (KIND_USERNAME, "Username"),
        (KIND_GOOGLE, "Google"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    account = models.ForeignKey(
        Account, on_delete=models.CASCADE, related_name="identifiers"
    )
    kind = models.CharField(max_length=16, choices=KINDS)
    value_hash = models.CharField(max_length=64, db_index=True)
    value_encrypted = models.TextField()
    verified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "accounts_identifier"
        constraints = [
            models.UniqueConstraint(
                fields=["kind", "value_hash"], name="unique_identifier_per_kind"
            )
        ]

    @property
    def value(self) -> str:
        return crypto.decrypt(self.value_encrypted)

    @property
    def is_verified(self) -> bool:
        return self.verified_at is not None

    @classmethod
    def create_for(cls, account, kind: str, value: str, verified: bool = False):
        return cls.objects.create(
            account=account,
            kind=kind,
            value_hash=crypto.blind_index(value),
            value_encrypted=crypto.encrypt(value),
            verified_at=timezone.now() if verified else None,
        )

    @classmethod
    def lookup(cls, kind: str, value: str):
        return cls.objects.filter(
            kind=kind, value_hash=crypto.blind_index(value)
        ).first()

    def __str__(self) -> str:
        return f"{self.kind} identifier for {self.account_id}"
```

- [ ] **Step 4: Extend `Device`**

Inside the existing `Device` class, after the `locale` field, add:

```python
    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="devices",
    )
    bound_at = models.DateTimeField(null=True, blank=True)
    label = models.CharField(max_length=120, blank=True, default="")
```

A null `account` is the entire difference between anonymous and signed-in. `CASCADE` implements the hard-delete constraint: deleting an account takes its devices with it.

- [ ] **Step 5: Generate and apply the migration**

```bash
uv run python manage.py makemigrations accounts
uv run python manage.py migrate
```

Expected: a migration creating `Account` and `Identifier` and adding three fields to `Device`. Open it and confirm it does exactly that and nothing else.

- [ ] **Step 6: Run the tests to verify they pass**

Run: `uv run pytest tests/test_account_models.py -v` — all 8 pass.
Run: `uv run pytest -q` — everything still passes, anonymous behaviour unchanged.
Run: `uv run ruff check .` — exit 0.

- [ ] **Step 7: Commit**

```bash
git add backend/ && git commit -m "feat(accounts): Account and Identifier models, device binding"
```

---

### Task 3: Email signup

**Files:**
- Create: `backend/apps/accounts/serializers.py`
- Create: `backend/apps/accounts/auth_views.py`
- Modify: `backend/apps/accounts/urls.py`
- Modify: `backend/config/settings.py` (throttle rates)
- Test: `backend/tests/test_signup_email.py`

**Interfaces:**
- Consumes: `Account`, `Identifier`, `Device` from Task 2
- Produces:
  - `POST /api/auth/signup/` accepting `{"email": str, "password": str}`; returns 201 `{"account_id": str}`
  - `apps.accounts.serializers.EmailSignupSerializer`
  - throttle scope `"auth"` at `20/hour`

- [ ] **Step 1: Write the failing test**

Create `backend/tests/test_signup_email.py`:

```python
import pytest
from django.test import Client

from apps.accounts.models import Account, Device, Identifier
from apps.accounts.tokens import generate_device_token, hash_device_token


@pytest.fixture
def device():
    raw = generate_device_token()
    return Device.objects.create(token_hash=hash_device_token(raw)), raw


@pytest.mark.django_db
def test_signup_creates_an_account_and_binds_the_calling_device(device):
    row, raw = device
    response = Client().post(
        "/api/auth/signup/",
        data={"email": "her@example.com", "password": "a-real-password"},
        content_type="application/json",
        headers={"x-device-token": raw},
    )

    assert response.status_code == 201
    account = Account.objects.get(id=response.json()["account_id"])

    row.refresh_from_db()
    assert row.account_id == account.id
    assert row.bound_at is not None


@pytest.mark.django_db
def test_signup_stores_the_email_unverified_and_never_in_plaintext(device):
    _, raw = device
    Client().post(
        "/api/auth/signup/",
        data={"email": "her@example.com", "password": "a-real-password"},
        content_type="application/json",
        headers={"x-device-token": raw},
    )

    identifier = Identifier.objects.get(kind=Identifier.KIND_EMAIL)
    assert identifier.is_verified is False
    assert "her@example.com" not in identifier.value_encrypted


@pytest.mark.django_db
def test_signup_never_returns_the_password_or_a_token(device):
    _, raw = device
    response = Client().post(
        "/api/auth/signup/",
        data={"email": "her@example.com", "password": "a-real-password"},
        content_type="application/json",
        headers={"x-device-token": raw},
    )
    assert set(response.json()) == {"account_id"}


@pytest.mark.django_db
def test_signup_rejects_a_duplicate_email(device):
    _, raw = device
    payload = {"email": "her@example.com", "password": "a-real-password"}
    Client().post(
        "/api/auth/signup/",
        data=payload,
        content_type="application/json",
        headers={"x-device-token": raw},
    )

    second_raw = generate_device_token()
    Device.objects.create(token_hash=hash_device_token(second_raw))
    response = Client().post(
        "/api/auth/signup/",
        data=payload,
        content_type="application/json",
        headers={"x-device-token": second_raw},
    )

    assert response.status_code == 400
    assert Account.objects.count() == 1


@pytest.mark.django_db
def test_signup_rejects_a_short_password(device):
    _, raw = device
    response = Client().post(
        "/api/auth/signup/",
        data={"email": "her@example.com", "password": "short"},
        content_type="application/json",
        headers={"x-device-token": raw},
    )
    assert response.status_code == 400
    assert Account.objects.count() == 0


@pytest.mark.django_db
def test_signup_requires_a_device_token():
    response = Client().post(
        "/api/auth/signup/",
        data={"email": "her@example.com", "password": "a-real-password"},
        content_type="application/json",
    )
    assert response.status_code == 401
    assert Account.objects.count() == 0


@pytest.mark.django_db
def test_a_device_already_bound_cannot_sign_up_again(device):
    row, raw = device
    payload = {"email": "her@example.com", "password": "a-real-password"}
    Client().post(
        "/api/auth/signup/",
        data=payload,
        content_type="application/json",
        headers={"x-device-token": raw},
    )

    response = Client().post(
        "/api/auth/signup/",
        data={"email": "other@example.com", "password": "a-real-password"},
        content_type="application/json",
        headers={"x-device-token": raw},
    )
    assert response.status_code == 409
    assert Account.objects.count() == 1
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest tests/test_signup_email.py -v`
Expected: FAIL — 404, because `/api/auth/signup/` does not exist.

- [ ] **Step 3: Write the serializer**

Create `backend/apps/accounts/serializers.py`:

```python
from rest_framework import serializers

from apps.accounts.models import Identifier

MIN_PASSWORD_LENGTH = 10


class EmailSignupSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(min_length=MIN_PASSWORD_LENGTH, write_only=True)

    def validate_email(self, value: str) -> str:
        if Identifier.lookup(Identifier.KIND_EMAIL, value) is not None:
            # Deliberately the same shape of error as any other validation
            # failure. This endpoint requires a device token, so it is not an
            # open oracle, but there is no reason to confirm an address more
            # loudly than necessary.
            raise serializers.ValidationError("This email cannot be used.")
        return value
```

- [ ] **Step 4: Write the view**

Create `backend/apps/accounts/auth_views.py`:

```python
from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, throttle_classes
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle

from apps.accounts.models import Account, Identifier
from apps.accounts.serializers import EmailSignupSerializer


@api_view(["POST"])
@throttle_classes([ScopedRateThrottle])
def signup(request):
    """Create an account and bind the calling device to it.

    The caller is already an anonymous device; signing up does not issue a new
    credential, it gives the existing one an owner.
    """
    device = request.auth
    if device.account_id is not None:
        return Response(
            {"detail": "This device is already signed in."},
            status=status.HTTP_409_CONFLICT,
        )

    serializer = EmailSignupSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    with transaction.atomic():
        account = Account()
        account.set_password(serializer.validated_data["password"])
        account.save()
        Identifier.create_for(
            account, Identifier.KIND_EMAIL, serializer.validated_data["email"]
        )
        device.account = account
        device.bound_at = timezone.now()
        device.save(update_fields=["account", "bound_at"])

    return Response({"account_id": str(account.id)}, status=status.HTTP_201_CREATED)


signup.cls.throttle_scope = "auth"
```

Note there is no `@permission_classes` decorator: the project default is already `IsAuthenticated`, and here that means "a valid device token", which is exactly the requirement.

- [ ] **Step 5: Route it**

Replace `backend/apps/accounts/urls.py` with:

```python
from django.urls import path

from apps.accounts import auth_views, views

urlpatterns = [
    path("devices/", views.create_device, name="create-device"),
    path("auth/signup/", auth_views.signup, name="auth-signup"),
]
```

- [ ] **Step 6: Add the throttle rate**

In `backend/config/settings.py`, inside `REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]`, add:

```python
        "auth": "20/hour",
```

- [ ] **Step 7: Run the tests to verify they pass**

Run: `uv run pytest tests/test_signup_email.py -v` — all 7 pass.
Run: `uv run pytest -q && uv run ruff check .` — everything green.

- [ ] **Step 8: Regenerate the committed schema**

The API surface changed, and a stale `schema.yml` fails its drift test.

```bash
uv run python manage.py spectacular --file schema.yml --validate --fail-on-warn
```

- [ ] **Step 9: Commit**

```bash
git add backend/ && git commit -m "feat(accounts): email signup binds the calling device"
```

---

### Task 4: Email verification

**Files:**
- Create: `backend/apps/accounts/verification.py`
- Modify: `backend/apps/accounts/auth_views.py`
- Modify: `backend/apps/accounts/urls.py`
- Modify: `backend/config/settings.py` (email backend, `ACCOUNT_VERIFICATION_URL`)
- Test: `backend/tests/test_email_verification.py`

**Interfaces:**
- Consumes: `Identifier` from Task 2, `signup` from Task 3
- Produces:
  - `apps.accounts.verification.make_token(identifier) -> str`
  - `apps.accounts.verification.read_token(token: str, max_age_seconds: int = 172800) -> uuid.UUID` — raises `django.core.signing.BadSignature` or `SignatureExpired`
  - `apps.accounts.verification.send_verification_email(identifier) -> None`
  - `POST /api/auth/verify-email/` accepting `{"token": str}`; 200 on success, 400 on bad or expired token

- [ ] **Step 1: Write the failing test**

Create `backend/tests/test_email_verification.py`:

```python
import pytest
from django.core import mail
from django.core.signing import SignatureExpired
from django.test import Client

from apps.accounts.models import Account, Identifier
from apps.accounts import verification


@pytest.fixture
def identifier(db):
    account = Account.objects.create()
    return Identifier.create_for(account, Identifier.KIND_EMAIL, "her@example.com")


@pytest.mark.django_db
def test_token_round_trips_to_the_identifier_id(identifier):
    token = verification.make_token(identifier)
    assert verification.read_token(token) == identifier.id


@pytest.mark.django_db
def test_an_expired_token_is_rejected(identifier):
    token = verification.make_token(identifier)
    with pytest.raises(SignatureExpired):
        verification.read_token(token, max_age_seconds=-1)


@pytest.mark.django_db
def test_verifying_marks_the_identifier_verified(identifier):
    token = verification.make_token(identifier)
    response = Client().post(
        "/api/auth/verify-email/",
        data={"token": token},
        content_type="application/json",
    )

    assert response.status_code == 200
    identifier.refresh_from_db()
    assert identifier.is_verified is True


@pytest.mark.django_db
def test_a_tampered_token_is_rejected(identifier):
    response = Client().post(
        "/api/auth/verify-email/",
        data={"token": "not-a-real-token"},
        content_type="application/json",
    )
    assert response.status_code == 400
    identifier.refresh_from_db()
    assert identifier.is_verified is False


@pytest.mark.django_db
def test_verification_needs_no_device_token(identifier):
    """She may open the link on a laptop that has never used the app."""
    token = verification.make_token(identifier)
    response = Client().post(
        "/api/auth/verify-email/",
        data={"token": token},
        content_type="application/json",
    )
    assert response.status_code == 200


@pytest.mark.django_db
def test_the_email_is_sent_and_contains_the_token_not_the_address(identifier):
    mail.outbox.clear()
    verification.send_verification_email(identifier)

    assert len(mail.outbox) == 1
    message = mail.outbox[0]
    assert message.to == ["her@example.com"]

    # The link must carry a token that actually verifies this identifier.
    token = message.body.split("token=")[1].split()[0]
    assert verification.read_token(token) == identifier.id
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest tests/test_email_verification.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'apps.accounts.verification'`

- [ ] **Step 3: Write the verification module**

Create `backend/apps/accounts/verification.py`:

```python
import uuid

from django.conf import settings
from django.core.mail import send_mail
from django.core.signing import TimestampSigner

SALT = "femopedia.email-verification"
DEFAULT_MAX_AGE_SECONDS = 172800  # two days


def make_token(identifier) -> str:
    """Sign the identifier's id. No database row is needed to issue or revoke:
    the signature and its timestamp carry everything."""
    return TimestampSigner(salt=SALT).sign(str(identifier.id))


def read_token(token: str, max_age_seconds: int = DEFAULT_MAX_AGE_SECONDS) -> uuid.UUID:
    raw = TimestampSigner(salt=SALT).unsign(token, max_age=max_age_seconds)
    return uuid.UUID(raw)


def send_verification_email(identifier) -> None:
    token = make_token(identifier)
    link = f"{settings.ACCOUNT_VERIFICATION_URL}?token={token}"
    send_mail(
        subject="Confirm your Femopedia email",
        message=(
            "Open this link to confirm your email address:\n\n"
            f"{link}\n\n"
            "If you did not create a Femopedia account, ignore this message."
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[identifier.value],
        fail_silently=False,
    )
```

- [ ] **Step 4: Add the settings**

Append to `backend/config/settings.py`:

```python
# Console backend in development; a real sending service is a launch
# dependency, since verification mail landing in spam breaks signup for
# anyone whose only route in is an email address.
EMAIL_BACKEND = env(
    "DJANGO_EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend"
)
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="noreply@femopedia.local")
ACCOUNT_VERIFICATION_URL = env(
    "ACCOUNT_VERIFICATION_URL", default="http://localhost:3000/verify-email"
)
```

Add the same three keys, with these default values, to `backend/.env.example`.

- [ ] **Step 5: Add the view and route**

Append to `backend/apps/accounts/auth_views.py` (imports at the top with the others):

```python
from django.core.signing import BadSignature
from rest_framework.permissions import AllowAny

from apps.accounts import verification


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([ScopedRateThrottle])
def verify_email(request):
    """Confirm an email address.

    Deliberately AllowAny: she may open the link on a device that has never
    used the application, and requiring a device token there would strand her.
    """
    token = request.data.get("token", "") if isinstance(request.data, dict) else ""
    try:
        identifier_id = verification.read_token(token)
    except BadSignature:
        return Response(
            {"detail": "This link is invalid or has expired."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    updated = Identifier.objects.filter(
        id=identifier_id, verified_at__isnull=True
    ).update(verified_at=timezone.now())

    if not updated and not Identifier.objects.filter(id=identifier_id).exists():
        return Response(
            {"detail": "This link is invalid or has expired."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    return Response({"status": "verified"})


verify_email.cls.throttle_scope = "auth"
```

`SignatureExpired` subclasses `BadSignature`, so one `except` covers both. Add `permission_classes` to the existing `rest_framework.decorators` import line.

In `backend/apps/accounts/urls.py`, add inside `urlpatterns`:

```python
    path("auth/verify-email/", auth_views.verify_email, name="auth-verify-email"),
```

- [ ] **Step 6: Send the mail on signup**

In `signup` in `backend/apps/accounts/auth_views.py`, capture the identifier and send after the transaction commits:

```python
        identifier = Identifier.create_for(
            account, Identifier.KIND_EMAIL, serializer.validated_data["email"]
        )
```

and after the `with transaction.atomic():` block, before the `return`:

```python
    verification.send_verification_email(identifier)
```

Sending outside the transaction means a mail failure cannot roll back an account that was successfully created.

- [ ] **Step 7: Run the tests to verify they pass**

Run: `uv run pytest tests/test_email_verification.py tests/test_signup_email.py -v` — all pass.
Run: `uv run pytest -q && uv run ruff check .` — green.
Regenerate the schema: `uv run python manage.py spectacular --file schema.yml --validate --fail-on-warn`

- [ ] **Step 8: Commit**

```bash
git add backend/ && git commit -m "feat(accounts): email verification by signed token"
```

---

### Task 5: Login and logout

**Files:**
- Modify: `backend/apps/accounts/serializers.py`
- Modify: `backend/apps/accounts/auth_views.py`
- Modify: `backend/apps/accounts/urls.py`
- Test: `backend/tests/test_login_logout.py`

**Interfaces:**
- Consumes: `Account`, `Identifier`, `Device`, `generate_device_token`, `hash_device_token`
- Produces:
  - `POST /api/auth/login/` accepting `{"email": str, "password": str}`; 200 `{"account_id": str}`, 401 on bad credentials
  - `POST /api/auth/logout/`; 200 `{"device_token": str}` — a fresh anonymous token
  - `apps.accounts.serializers.LoginSerializer`

- [ ] **Step 1: Write the failing test**

Create `backend/tests/test_login_logout.py`:

```python
import pytest
from django.test import Client

from apps.accounts.models import Account, Device, Identifier
from apps.accounts.tokens import generate_device_token, hash_device_token

PASSWORD = "a-real-password"


@pytest.fixture
def account(db):
    account = Account.objects.create()
    account.set_password(PASSWORD)
    account.save()
    Identifier.create_for(account, Identifier.KIND_EMAIL, "her@example.com", verified=True)
    return account


def new_device():
    raw = generate_device_token()
    return Device.objects.create(token_hash=hash_device_token(raw)), raw


@pytest.mark.django_db
def test_login_binds_the_calling_device(account):
    device, raw = new_device()
    response = Client().post(
        "/api/auth/login/",
        data={"email": "her@example.com", "password": PASSWORD},
        content_type="application/json",
        headers={"x-device-token": raw},
    )

    assert response.status_code == 200
    device.refresh_from_db()
    assert device.account_id == account.id


@pytest.mark.django_db
def test_a_second_device_reaches_the_same_account(account):
    first, first_raw = new_device()
    second, second_raw = new_device()
    payload = {"email": "her@example.com", "password": PASSWORD}

    for raw in (first_raw, second_raw):
        Client().post(
            "/api/auth/login/",
            data=payload,
            content_type="application/json",
            headers={"x-device-token": raw},
        )

    first.refresh_from_db()
    second.refresh_from_db()
    assert first.account_id == second.account_id == account.id


@pytest.mark.django_db
def test_a_wrong_password_is_rejected_and_binds_nothing(account):
    device, raw = new_device()
    response = Client().post(
        "/api/auth/login/",
        data={"email": "her@example.com", "password": "wrong-password"},
        content_type="application/json",
        headers={"x-device-token": raw},
    )

    assert response.status_code == 401
    device.refresh_from_db()
    assert device.account_id is None


@pytest.mark.django_db
def test_an_unknown_email_answers_exactly_like_a_wrong_password(account):
    device, raw = new_device()
    unknown = Client().post(
        "/api/auth/login/",
        data={"email": "nobody@example.com", "password": PASSWORD},
        content_type="application/json",
        headers={"x-device-token": raw},
    )
    wrong = Client().post(
        "/api/auth/login/",
        data={"email": "her@example.com", "password": "wrong-password"},
        content_type="application/json",
        headers={"x-device-token": raw},
    )

    # Differing answers would tell anyone who asks whether a given woman has
    # an account here.
    assert unknown.status_code == wrong.status_code == 401
    assert unknown.json() == wrong.json()


@pytest.mark.django_db
def test_logout_issues_a_fresh_anonymous_token_and_destroys_the_old_device(account):
    device, raw = new_device()
    Client().post(
        "/api/auth/login/",
        data={"email": "her@example.com", "password": PASSWORD},
        content_type="application/json",
        headers={"x-device-token": raw},
    )

    response = Client().post("/api/auth/logout/", headers={"x-device-token": raw})
    assert response.status_code == 200

    new_token = response.json()["device_token"]
    assert new_token != raw
    assert not Device.objects.filter(id=device.id).exists()

    fresh = Device.objects.get(token_hash=hash_device_token(new_token))
    assert fresh.account_id is None


@pytest.mark.django_db
def test_the_old_token_stops_working_after_logout(account):
    _, raw = new_device()
    Client().post(
        "/api/auth/login/",
        data={"email": "her@example.com", "password": PASSWORD},
        content_type="application/json",
        headers={"x-device-token": raw},
    )
    Client().post("/api/auth/logout/", headers={"x-device-token": raw})

    assert Client().get("/api/whoami/", headers={"x-device-token": raw}).status_code == 401
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest tests/test_login_logout.py -v`
Expected: FAIL — 404 on `/api/auth/login/`.

- [ ] **Step 3: Add the serializer**

Append to `backend/apps/accounts/serializers.py`:

```python
class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
```

No `min_length` here: length rules belong at signup, and enforcing them at login would tell an attacker which passwords are too short to be real.

- [ ] **Step 4: Write the views**

Append to `backend/apps/accounts/auth_views.py`:

```python
from apps.accounts.serializers import LoginSerializer
from apps.accounts.tokens import generate_device_token, hash_device_token

INVALID_CREDENTIALS = {"detail": "Email or password is incorrect."}


@api_view(["POST"])
@throttle_classes([ScopedRateThrottle])
def login(request):
    serializer = LoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    identifier = Identifier.lookup(
        Identifier.KIND_EMAIL, serializer.validated_data["email"]
    )
    account = identifier.account if identifier else None

    # One response for "no such account" and "wrong password", so the endpoint
    # cannot be used to discover whether a given woman has an account here.
    if account is None or not account.check_password(
        serializer.validated_data["password"]
    ):
        return Response(INVALID_CREDENTIALS, status=status.HTTP_401_UNAUTHORIZED)

    device = request.auth
    device.account = account
    device.bound_at = timezone.now()
    device.save(update_fields=["account", "bound_at"])

    return Response({"account_id": str(account.id)})


@api_view(["POST"])
@throttle_classes([ScopedRateThrottle])
def logout(request):
    """Delete this device and issue a fresh anonymous one.

    Not merely unbinding: on a shared phone, signing out must leave an
    application with nothing in it, rather than a sign-in screen with her
    history one tap behind it.
    """
    old_device = request.auth
    raw_token = generate_device_token()

    with transaction.atomic():
        new_device = Device.objects.create(
            token_hash=hash_device_token(raw_token), locale=old_device.locale
        )
        old_device.delete()

    return Response({"device_token": raw_token, "device_id": str(new_device.id)})


login.cls.throttle_scope = "auth"
logout.cls.throttle_scope = "auth"
```

Add `Device` to the `apps.accounts.models` import line at the top of the file.

- [ ] **Step 5: Route them**

Add to `urlpatterns` in `backend/apps/accounts/urls.py`:

```python
    path("auth/login/", auth_views.login, name="auth-login"),
    path("auth/logout/", auth_views.logout, name="auth-logout"),
```

- [ ] **Step 6: Run the tests to verify they pass**

Run: `uv run pytest tests/test_login_logout.py -v` — all 6 pass.
Run: `uv run pytest -q && uv run ruff check .` — green.
Regenerate the schema.

- [ ] **Step 7: Commit**

```bash
git add backend/ && git commit -m "feat(accounts): login binds a device, logout leaves nothing behind"
```

---

### Task 6: Contact-less accounts and recovery codes

**Files:**
- Modify: `backend/apps/accounts/tokens.py`
- Modify: `backend/apps/accounts/serializers.py`
- Modify: `backend/apps/accounts/auth_views.py`
- Modify: `backend/apps/accounts/urls.py`
- Test: `backend/tests/test_contactless_account.py`

**Interfaces:**
- Consumes: everything from Tasks 2–5
- Produces:
  - `apps.accounts.tokens.generate_recovery_code() -> str` — 6 groups of 4 uppercase characters, hyphen-separated
  - `apps.accounts.tokens.hash_recovery_code(raw: str) -> str` — 64-char SHA-256 hex of the normalised code
  - `POST /api/auth/signup/` additionally accepting `{"username": str, "password": str}`; returns 201 `{"account_id": str, "recovery_code": str}`
  - `POST /api/auth/recover/` accepting `{"username": str, "recovery_code": str, "new_password": str}`; 200 `{"recovery_code": str}` — the replacement

- [ ] **Step 1: Write the failing test**

Create `backend/tests/test_contactless_account.py`:

```python
import pytest
from django.test import Client

from apps.accounts.models import Account, Device, Identifier
from apps.accounts.tokens import (
    generate_device_token,
    generate_recovery_code,
    hash_device_token,
    hash_recovery_code,
)


def new_device():
    raw = generate_device_token()
    return Device.objects.create(token_hash=hash_device_token(raw)), raw


def test_recovery_codes_are_unique_and_grouped():
    codes = {generate_recovery_code() for _ in range(200)}
    assert len(codes) == 200
    sample = generate_recovery_code()
    assert len(sample.split("-")) == 6
    assert sample == sample.upper()


def test_recovery_code_hash_ignores_case_and_spacing():
    code = "ABCD-EFGH-IJKL-MNOP-QRST-UVWX"
    assert hash_recovery_code(code) == hash_recovery_code(" abcd-efgh-ijkl-mnop-qrst-uvwx ")
    assert len(hash_recovery_code(code)) == 64


@pytest.mark.django_db
def test_username_signup_returns_the_recovery_code_exactly_once():
    _, raw = new_device()
    response = Client().post(
        "/api/auth/signup/",
        data={"username": "sunita", "password": "a-real-password"},
        content_type="application/json",
        headers={"x-device-token": raw},
    )

    assert response.status_code == 201
    body = response.json()
    assert set(body) == {"account_id", "recovery_code"}

    account = Account.objects.get(id=body["account_id"])
    assert account.recovery_code_hash == hash_recovery_code(body["recovery_code"])
    assert body["recovery_code"] not in account.recovery_code_hash


@pytest.mark.django_db
def test_username_signup_stores_no_email_identifier():
    _, raw = new_device()
    Client().post(
        "/api/auth/signup/",
        data={"username": "sunita", "password": "a-real-password"},
        content_type="application/json",
        headers={"x-device-token": raw},
    )
    assert Identifier.objects.filter(kind=Identifier.KIND_EMAIL).count() == 0
    assert Identifier.objects.filter(kind=Identifier.KIND_USERNAME).count() == 1


@pytest.mark.django_db
def test_signup_rejects_a_payload_with_neither_email_nor_username():
    _, raw = new_device()
    response = Client().post(
        "/api/auth/signup/",
        data={"password": "a-real-password"},
        content_type="application/json",
        headers={"x-device-token": raw},
    )
    assert response.status_code == 400
    assert Account.objects.count() == 0


@pytest.mark.django_db
def test_recovery_sets_a_new_password_and_replaces_the_code():
    _, raw = new_device()
    signup = Client().post(
        "/api/auth/signup/",
        data={"username": "sunita", "password": "a-real-password"},
        content_type="application/json",
        headers={"x-device-token": raw},
    ).json()

    response = Client().post(
        "/api/auth/recover/",
        data={
            "username": "sunita",
            "recovery_code": signup["recovery_code"],
            "new_password": "a-brand-new-password",
        },
        content_type="application/json",
    )

    assert response.status_code == 200
    replacement = response.json()["recovery_code"]
    assert replacement != signup["recovery_code"]

    account = Account.objects.get(id=signup["account_id"])
    assert account.check_password("a-brand-new-password") is True
    assert account.recovery_code_hash == hash_recovery_code(replacement)


@pytest.mark.django_db
def test_a_used_recovery_code_cannot_be_used_again():
    _, raw = new_device()
    signup = Client().post(
        "/api/auth/signup/",
        data={"username": "sunita", "password": "a-real-password"},
        content_type="application/json",
        headers={"x-device-token": raw},
    ).json()

    payload = {
        "username": "sunita",
        "recovery_code": signup["recovery_code"],
        "new_password": "a-brand-new-password",
    }
    Client().post("/api/auth/recover/", data=payload, content_type="application/json")
    second = Client().post(
        "/api/auth/recover/", data=payload, content_type="application/json"
    )

    assert second.status_code == 400


@pytest.mark.django_db
def test_recovery_answers_identically_for_an_unknown_username():
    unknown = Client().post(
        "/api/auth/recover/",
        data={
            "username": "nobody",
            "recovery_code": "ABCD-EFGH-IJKL-MNOP-QRST-UVWX",
            "new_password": "a-brand-new-password",
        },
        content_type="application/json",
    )
    assert unknown.status_code == 400
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest tests/test_contactless_account.py -v`
Expected: FAIL — `ImportError: cannot import name 'generate_recovery_code'`

- [ ] **Step 3: Add the code helpers**

Append to `backend/apps/accounts/tokens.py`:

```python
RECOVERY_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # no I, O, 0, 1
RECOVERY_GROUPS = 6
RECOVERY_GROUP_LENGTH = 4


def generate_recovery_code() -> str:
    """Return a recovery code she is expected to write down.

    Grouped and drawn from an alphabet without visually ambiguous characters,
    because this is transcribed by hand under stress.
    """
    groups = [
        "".join(secrets.choice(RECOVERY_ALPHABET) for _ in range(RECOVERY_GROUP_LENGTH))
        for _ in range(RECOVERY_GROUPS)
    ]
    return "-".join(groups)


def hash_recovery_code(raw: str) -> str:
    """Hash the normalised code. Only the hash is ever stored."""
    normalised = raw.strip().upper().replace(" ", "")
    return hashlib.sha256(normalised.encode("utf-8")).hexdigest()
```

- [ ] **Step 4: Add the serializers**

Append to `backend/apps/accounts/serializers.py`:

```python
class UsernameSignupSerializer(serializers.Serializer):
    username = serializers.RegexField(r"^[a-zA-Z0-9_.-]{3,32}$")
    password = serializers.CharField(min_length=MIN_PASSWORD_LENGTH, write_only=True)

    def validate_username(self, value: str) -> str:
        if Identifier.lookup(Identifier.KIND_USERNAME, value) is not None:
            raise serializers.ValidationError("This username cannot be used.")
        return value


class RecoverySerializer(serializers.Serializer):
    username = serializers.CharField()
    recovery_code = serializers.CharField()
    new_password = serializers.CharField(min_length=MIN_PASSWORD_LENGTH, write_only=True)
```

- [ ] **Step 5: Branch signup and add recovery**

In `backend/apps/accounts/auth_views.py`, replace the body of `signup` after the already-signed-in check with:

```python
    payload = request.data if isinstance(request.data, dict) else {}
    if "email" in payload:
        serializer = EmailSignupSerializer(data=payload)
    elif "username" in payload:
        serializer = UsernameSignupSerializer(data=payload)
    else:
        return Response(
            {"detail": "Provide either an email or a username."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    serializer.is_valid(raise_exception=True)

    recovery_code = None
    with transaction.atomic():
        account = Account()
        account.set_password(serializer.validated_data["password"])
        if isinstance(serializer, UsernameSignupSerializer):
            recovery_code = generate_recovery_code()
            account.recovery_code_hash = hash_recovery_code(recovery_code)
        account.save()

        if isinstance(serializer, EmailSignupSerializer):
            identifier = Identifier.create_for(
                account, Identifier.KIND_EMAIL, serializer.validated_data["email"]
            )
        else:
            identifier = None
            Identifier.create_for(
                account, Identifier.KIND_USERNAME, serializer.validated_data["username"]
            )

        device.account = account
        device.bound_at = timezone.now()
        device.save(update_fields=["account", "bound_at"])

    if identifier is not None:
        verification.send_verification_email(identifier)

    body = {"account_id": str(account.id)}
    if recovery_code is not None:
        body["recovery_code"] = recovery_code
    return Response(body, status=status.HTTP_201_CREATED)
```

Then append the recovery view:

```python
@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([ScopedRateThrottle])
def recover(request):
    """Set a new password using a recovery code, and issue a replacement code.

    AllowAny because a woman recovering an account may be on a new device that
    has no token yet. Every failure answers identically, so the endpoint cannot
    be used to discover which usernames exist.
    """
    serializer = RecoverySerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    failure = Response(
        {"detail": "That username and recovery code do not match."},
        status=status.HTTP_400_BAD_REQUEST,
    )

    identifier = Identifier.lookup(
        Identifier.KIND_USERNAME, serializer.validated_data["username"]
    )
    if identifier is None:
        return failure

    account = identifier.account
    supplied = hash_recovery_code(serializer.validated_data["recovery_code"])
    if not account.recovery_code_hash or not secrets.compare_digest(
        supplied, account.recovery_code_hash
    ):
        return failure

    replacement = generate_recovery_code()
    account.set_password(serializer.validated_data["new_password"])
    account.recovery_code_hash = hash_recovery_code(replacement)
    account.recovery_code_used_at = timezone.now()
    account.save(
        update_fields=["password", "recovery_code_hash", "recovery_code_used_at"]
    )

    return Response({"recovery_code": replacement})


recover.cls.throttle_scope = "auth"
```

Add to the imports at the top of the file: `import secrets`, `UsernameSignupSerializer`, `RecoverySerializer`, `generate_recovery_code`, `hash_recovery_code`.

- [ ] **Step 6: Route recovery**

Add to `urlpatterns`:

```python
    path("auth/recover/", auth_views.recover, name="auth-recover"),
```

- [ ] **Step 7: Run the tests to verify they pass**

Run: `uv run pytest tests/test_contactless_account.py -v` — all 8 pass.
Run: `uv run pytest -q && uv run ruff check .` — green.
Regenerate the schema.

- [ ] **Step 8: Commit**

```bash
git add backend/ && git commit -m "feat(accounts): contact-less accounts with recovery codes"
```

---

### Task 7: Password reset by email, and password change

**Files:**
- Modify: `backend/apps/accounts/verification.py`
- Modify: `backend/apps/accounts/serializers.py`
- Modify: `backend/apps/accounts/auth_views.py`
- Modify: `backend/apps/accounts/urls.py`
- Modify: `backend/config/settings.py` (`ACCOUNT_PASSWORD_RESET_URL`)
- Test: `backend/tests/test_password.py`

**Interfaces:**
- Consumes: Tasks 2–6
- Produces:
  - `apps.accounts.verification.make_reset_token(account) -> str`, `read_reset_token(token, max_age_seconds=3600) -> uuid.UUID`, `send_password_reset_email(identifier) -> None`
  - `POST /api/auth/password-reset/` accepting `{"email": str}`; always 202
  - `POST /api/auth/password-reset/confirm/` accepting `{"token": str, "new_password": str}`; 200 or 400
  - `POST /api/account/password/` accepting `{"current_password": str, "new_password": str}`; 200 or 400

- [ ] **Step 1: Write the failing test**

Create `backend/tests/test_password.py`:

```python
import pytest
from django.core import mail
from django.test import Client

from apps.accounts.models import Account, Device, Identifier
from apps.accounts import verification
from apps.accounts.tokens import generate_device_token, hash_device_token

PASSWORD = "a-real-password"


@pytest.fixture
def account(db):
    account = Account.objects.create()
    account.set_password(PASSWORD)
    account.save()
    Identifier.create_for(account, Identifier.KIND_EMAIL, "her@example.com", verified=True)
    return account


def bound_device(account):
    raw = generate_device_token()
    Device.objects.create(token_hash=hash_device_token(raw), account=account)
    return raw


@pytest.mark.django_db
def test_reset_request_answers_the_same_whether_or_not_the_address_exists(account):
    mail.outbox.clear()
    known = Client().post(
        "/api/auth/password-reset/",
        data={"email": "her@example.com"},
        content_type="application/json",
    )
    unknown = Client().post(
        "/api/auth/password-reset/",
        data={"email": "nobody@example.com"},
        content_type="application/json",
    )

    # A differing response would tell anyone who asks whether a given woman
    # has an account here.
    assert known.status_code == unknown.status_code == 202
    assert known.json() == unknown.json()
    assert len(mail.outbox) == 1


@pytest.mark.django_db
def test_reset_confirm_changes_the_password(account):
    token = verification.make_reset_token(account)
    response = Client().post(
        "/api/auth/password-reset/confirm/",
        data={"token": token, "new_password": "a-brand-new-password"},
        content_type="application/json",
    )

    assert response.status_code == 200
    account.refresh_from_db()
    assert account.check_password("a-brand-new-password") is True
    assert account.check_password(PASSWORD) is False


@pytest.mark.django_db
def test_a_reset_token_cannot_be_reused(account):
    token = verification.make_reset_token(account)
    payload = {"token": token, "new_password": "a-brand-new-password"}
    Client().post(
        "/api/auth/password-reset/confirm/", data=payload, content_type="application/json"
    )
    second = Client().post(
        "/api/auth/password-reset/confirm/", data=payload, content_type="application/json"
    )

    # The token signs the current password hash, so changing the password
    # invalidates every token issued before it.
    assert second.status_code == 400


@pytest.mark.django_db
def test_an_unverified_email_gets_no_reset_mail():
    account = Account.objects.create()
    account.set_password(PASSWORD)
    account.save()
    Identifier.create_for(account, Identifier.KIND_EMAIL, "unverified@example.com")

    mail.outbox.clear()
    response = Client().post(
        "/api/auth/password-reset/",
        data={"email": "unverified@example.com"},
        content_type="application/json",
    )

    assert response.status_code == 202
    assert len(mail.outbox) == 0


@pytest.mark.django_db
def test_password_change_requires_the_current_password(account):
    raw = bound_device(account)
    wrong = Client().post(
        "/api/account/password/",
        data={"current_password": "not-it", "new_password": "a-brand-new-password"},
        content_type="application/json",
        headers={"x-device-token": raw},
    )
    assert wrong.status_code == 400

    right = Client().post(
        "/api/account/password/",
        data={"current_password": PASSWORD, "new_password": "a-brand-new-password"},
        content_type="application/json",
        headers={"x-device-token": raw},
    )
    assert right.status_code == 200
    account.refresh_from_db()
    assert account.check_password("a-brand-new-password") is True


@pytest.mark.django_db
def test_an_anonymous_device_cannot_change_a_password():
    raw = generate_device_token()
    Device.objects.create(token_hash=hash_device_token(raw))
    response = Client().post(
        "/api/account/password/",
        data={"current_password": PASSWORD, "new_password": "a-brand-new-password"},
        content_type="application/json",
        headers={"x-device-token": raw},
    )
    assert response.status_code == 403
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest tests/test_password.py -v`
Expected: FAIL — `AttributeError: module 'apps.accounts.verification' has no attribute 'make_reset_token'`

- [ ] **Step 3: Add reset tokens**

Append to `backend/apps/accounts/verification.py`:

```python
RESET_SALT = "femopedia.password-reset"
RESET_MAX_AGE_SECONDS = 3600


def make_reset_token(account) -> str:
    """Sign the account id together with a fingerprint of the current password.

    Signing the hash means changing the password invalidates every reset token
    issued before it, so a link cannot be replayed after it has been used.
    """
    fingerprint = sha256(account.password.encode("utf-8")).hexdigest()[:16]
    return TimestampSigner(salt=RESET_SALT).sign(f"{account.id}:{fingerprint}")


def read_reset_token(token: str, max_age_seconds: int = RESET_MAX_AGE_SECONDS):
    raw = TimestampSigner(salt=RESET_SALT).unsign(token, max_age=max_age_seconds)
    account_id, fingerprint = raw.rsplit(":", 1)
    return uuid.UUID(account_id), fingerprint


def send_password_reset_email(identifier) -> None:
    token = make_reset_token(identifier.account)
    link = f"{settings.ACCOUNT_PASSWORD_RESET_URL}?token={token}"
    send_mail(
        subject="Reset your Femopedia password",
        message=(
            "Open this link within one hour to choose a new password:\n\n"
            f"{link}\n\n"
            "If you did not ask for this, ignore this message."
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[identifier.value],
        fail_silently=False,
    )
```

Add `from hashlib import sha256` to the imports at the top of the file.

- [ ] **Step 4: Add the setting**

Append to `backend/config/settings.py`, and add the same key and default to `backend/.env.example`:

```python
ACCOUNT_PASSWORD_RESET_URL = env(
    "ACCOUNT_PASSWORD_RESET_URL", default="http://localhost:3000/reset-password"
)
```

- [ ] **Step 5: Add the serializers**

Append to `backend/apps/accounts/serializers.py`:

```python
class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    token = serializers.CharField()
    new_password = serializers.CharField(min_length=MIN_PASSWORD_LENGTH, write_only=True)


class PasswordChangeSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(min_length=MIN_PASSWORD_LENGTH, write_only=True)
```

- [ ] **Step 6: Write the views**

Append to `backend/apps/accounts/auth_views.py`:

```python
from hashlib import sha256

from apps.accounts.serializers import (
    PasswordChangeSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
)


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([ScopedRateThrottle])
def password_reset(request):
    """Always answer 202, whatever happens.

    Any difference between "sent" and "no such address" turns this endpoint
    into a way to ask whether a given woman has an account here.
    """
    serializer = PasswordResetRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    identifier = Identifier.lookup(
        Identifier.KIND_EMAIL, serializer.validated_data["email"]
    )
    if identifier is not None and identifier.is_verified:
        verification.send_password_reset_email(identifier)

    return Response({"status": "sent"}, status=status.HTTP_202_ACCEPTED)


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([ScopedRateThrottle])
def password_reset_confirm(request):
    serializer = PasswordResetConfirmSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    failure = Response(
        {"detail": "This link is invalid or has expired."},
        status=status.HTTP_400_BAD_REQUEST,
    )

    try:
        account_id, fingerprint = verification.read_reset_token(
            serializer.validated_data["token"]
        )
    except BadSignature:
        return failure

    account = Account.objects.filter(id=account_id).first()
    if account is None:
        return failure
    if sha256(account.password.encode("utf-8")).hexdigest()[:16] != fingerprint:
        return failure

    account.set_password(serializer.validated_data["new_password"])
    account.save(update_fields=["password"])
    return Response({"status": "changed"})


@api_view(["POST"])
@throttle_classes([ScopedRateThrottle])
def password_change(request):
    account = request.auth.account
    if account is None:
        return Response(
            {"detail": "This device is not signed in."},
            status=status.HTTP_403_FORBIDDEN,
        )

    serializer = PasswordChangeSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    if not account.check_password(serializer.validated_data["current_password"]):
        return Response(
            {"detail": "Current password is incorrect."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    account.set_password(serializer.validated_data["new_password"])
    account.save(update_fields=["password"])
    return Response({"status": "changed"})


password_reset.cls.throttle_scope = "auth"
password_reset_confirm.cls.throttle_scope = "auth"
password_change.cls.throttle_scope = "auth"
```

- [ ] **Step 7: Route them**

Add to `urlpatterns`:

```python
    path("auth/password-reset/", auth_views.password_reset, name="auth-password-reset"),
    path(
        "auth/password-reset/confirm/",
        auth_views.password_reset_confirm,
        name="auth-password-reset-confirm",
    ),
    path("account/password/", auth_views.password_change, name="account-password"),
```

- [ ] **Step 8: Run the tests to verify they pass**

Run: `uv run pytest tests/test_password.py -v` — all 6 pass.
Run: `uv run pytest -q && uv run ruff check .` — green.
Regenerate the schema.

- [ ] **Step 9: Commit**

```bash
git add backend/ && git commit -m "feat(accounts): password reset by email and password change"
```

---

### Task 8: Session list and remote revocation

**Files:**
- Create: `backend/apps/accounts/account_views.py`
- Modify: `backend/apps/accounts/authentication.py`
- Modify: `backend/apps/accounts/urls.py`
- Test: `backend/tests/test_sessions.py`

**Interfaces:**
- Consumes: Tasks 2–7
- Produces:
  - `GET /api/account/` returning `{"account_id", "created_at", "identifiers": [{"kind", "verified"}]}`
  - `GET /api/account/devices/` returning `{"devices": [{"id", "label", "last_seen", "bound_at", "is_current"}]}`
  - `DELETE /api/account/devices/{device_id}/` returning 204
  - `Device.label` populated from the User-Agent on authentication

- [ ] **Step 1: Write the failing test**

Create `backend/tests/test_sessions.py`:

```python
import pytest
from django.test import Client

from apps.accounts.models import Account, Device, Identifier
from apps.accounts.tokens import generate_device_token, hash_device_token


@pytest.fixture
def account(db):
    account = Account.objects.create()
    account.set_password("a-real-password")
    account.save()
    Identifier.create_for(account, Identifier.KIND_EMAIL, "her@example.com", verified=True)
    return account


def bound_device(account, label=""):
    raw = generate_device_token()
    device = Device.objects.create(
        token_hash=hash_device_token(raw), account=account, label=label
    )
    return device, raw


@pytest.mark.django_db
def test_account_summary_names_identifier_kinds_but_never_their_values(account):
    _, raw = bound_device(account)
    response = Client().get("/api/account/", headers={"x-device-token": raw})

    assert response.status_code == 200
    body = response.json()
    assert body["account_id"] == str(account.id)
    assert body["identifiers"] == [{"kind": "email", "verified": True}]
    assert "her@example.com" not in response.content.decode()


@pytest.mark.django_db
def test_device_list_shows_every_bound_device_and_marks_the_caller(account):
    first, first_raw = bound_device(account, label="Phone")
    second, _ = bound_device(account, label="Laptop")

    response = Client().get("/api/account/devices/", headers={"x-device-token": first_raw})
    devices = {d["id"]: d for d in response.json()["devices"]}

    assert set(devices) == {str(first.id), str(second.id)}
    assert devices[str(first.id)]["is_current"] is True
    assert devices[str(second.id)]["is_current"] is False


@pytest.mark.django_db
def test_device_list_never_exposes_a_token_hash(account):
    _, raw = bound_device(account)
    response = Client().get("/api/account/devices/", headers={"x-device-token": raw})
    device = Device.objects.get(account=account)
    assert device.token_hash not in response.content.decode()


@pytest.mark.django_db
def test_revoking_another_device_deletes_it(account):
    _, raw = bound_device(account)
    other, other_raw = bound_device(account)

    response = Client().delete(
        f"/api/account/devices/{other.id}/", headers={"x-device-token": raw}
    )

    assert response.status_code == 204
    assert not Device.objects.filter(id=other.id).exists()
    assert Client().get("/api/whoami/", headers={"x-device-token": other_raw}).status_code == 401


@pytest.mark.django_db
def test_a_device_belonging_to_another_account_cannot_be_revoked(account):
    _, raw = bound_device(account)

    stranger = Account.objects.create()
    their_device, _ = bound_device(stranger)

    response = Client().delete(
        f"/api/account/devices/{their_device.id}/", headers={"x-device-token": raw}
    )

    assert response.status_code == 404
    assert Device.objects.filter(id=their_device.id).exists()


@pytest.mark.django_db
def test_an_anonymous_device_has_no_account_endpoints():
    raw = generate_device_token()
    Device.objects.create(token_hash=hash_device_token(raw))
    assert Client().get("/api/account/", headers={"x-device-token": raw}).status_code == 403


@pytest.mark.django_db
def test_authentication_records_a_device_label(account):
    _, raw = bound_device(account)
    Client().get(
        "/api/whoami/",
        headers={"x-device-token": raw, "user-agent": "Mozilla/5.0 (Linux; Android 14)"},
    )
    device = Device.objects.get(account=account)
    assert "Android" in device.label
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest tests/test_sessions.py -v`
Expected: FAIL — 404 on `/api/account/`.

- [ ] **Step 3: Record a label on authentication**

In `backend/apps/accounts/authentication.py`, replace the `last_seen` update line with:

```python
        label = (request.META.get("HTTP_USER_AGENT") or "")[:120]
        Device.objects.filter(pk=device.pk).update(
            last_seen=timezone.now(), label=label
        )
```

The label is only ever shown back to the woman who owns the device, so she can tell one row in her session list from another.

- [ ] **Step 4: Write the views**

Create `backend/apps/accounts/account_views.py`:

```python
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from apps.accounts.models import Device


def _require_account(request):
    """Return the caller's account, or None when the device is anonymous."""
    return request.auth.account


@api_view(["GET"])
def account_summary(request):
    account = _require_account(request)
    if account is None:
        return Response(
            {"detail": "This device is not signed in."},
            status=status.HTTP_403_FORBIDDEN,
        )

    # Kinds and verification status only. The values themselves are encrypted
    # at rest and there is no reason for a summary screen to decrypt them.
    identifiers = [
        {"kind": i.kind, "verified": i.is_verified}
        for i in account.identifiers.order_by("created_at")
    ]
    return Response(
        {
            "account_id": str(account.id),
            "created_at": account.created_at.isoformat(),
            "identifiers": identifiers,
        }
    )


@api_view(["GET"])
def device_list(request):
    account = _require_account(request)
    if account is None:
        return Response(
            {"detail": "This device is not signed in."},
            status=status.HTTP_403_FORBIDDEN,
        )

    current_id = request.auth.id
    devices = [
        {
            "id": str(device.id),
            "label": device.label,
            "last_seen": device.last_seen.isoformat(),
            "bound_at": device.bound_at.isoformat() if device.bound_at else None,
            "is_current": device.id == current_id,
        }
        for device in account.devices.order_by("-last_seen")
    ]
    return Response({"devices": devices})


@api_view(["DELETE"])
def device_revoke(request, device_id):
    account = _require_account(request)
    if account is None:
        return Response(
            {"detail": "This device is not signed in."},
            status=status.HTTP_403_FORBIDDEN,
        )

    # Scoped to her own devices: a device belonging to someone else must be
    # indistinguishable from one that does not exist.
    deleted, _ = Device.objects.filter(id=device_id, account=account).delete()
    if not deleted:
        return Response(
            {"detail": "No such device."}, status=status.HTTP_404_NOT_FOUND
        )
    return Response(status=status.HTTP_204_NO_CONTENT)
```

Each handler builds its own `Response`. A shared module-level instance would be reused across requests, which DRF does not support.

- [ ] **Step 5: Route them**

Add to `urlpatterns` in `backend/apps/accounts/urls.py`, with `account_views` added to the import line:

```python
    path("account/", account_views.account_summary, name="account-summary"),
    path("account/devices/", account_views.device_list, name="account-devices"),
    path(
        "account/devices/<uuid:device_id>/",
        account_views.device_revoke,
        name="account-device-revoke",
    ),
```

- [ ] **Step 6: Run the tests to verify they pass**

Run: `uv run pytest tests/test_sessions.py -v` — all 7 pass.
Run: `uv run pytest -q && uv run ruff check .` — green.
Regenerate the schema.

- [ ] **Step 7: Commit**

```bash
git add backend/ && git commit -m "feat(accounts): session list and remote device revocation"
```

---

### Task 9: Export and deletion, proved complete by enumeration

**Files:**
- Create: `backend/apps/accounts/data_rights.py`
- Modify: `backend/apps/accounts/account_views.py`
- Modify: `backend/apps/accounts/serializers.py`
- Modify: `backend/apps/accounts/urls.py`
- Test: `backend/tests/test_data_rights.py`

**Interfaces:**
- Consumes: Tasks 2–8
- Produces:
  - `apps.accounts.data_rights.EXPORTED_MODELS: tuple[str, ...]` — dotted `app_label.ModelName` strings covered by the export
  - `apps.accounts.data_rights.build_export(account) -> dict`
  - `POST /api/account/export/` returning the export as JSON with `Content-Disposition: attachment`
  - `POST /api/account/delete/` accepting `{"password": str}`; 204 on success

- [ ] **Step 1: Write the failing test**

Create `backend/tests/test_data_rights.py`:

```python
import json

import pytest
from django.apps import apps
from django.test import Client

from apps.accounts.data_rights import EXPORTED_MODELS, build_export
from apps.accounts.models import Account, Device, Identifier
from apps.accounts.tokens import generate_device_token, hash_device_token

PASSWORD = "a-real-password"


@pytest.fixture
def account(db):
    account = Account.objects.create()
    account.set_password(PASSWORD)
    account.save()
    Identifier.create_for(account, Identifier.KIND_EMAIL, "her@example.com", verified=True)
    return account


def bound_device(account):
    raw = generate_device_token()
    return Device.objects.create(token_hash=hash_device_token(raw), account=account), raw


def models_referencing_account():
    """Every model with a relation to Account, by dotted label."""
    found = set()
    for model in apps.get_models():
        for field in model._meta.get_fields():
            related = getattr(field, "related_model", None)
            if related is Account and field.concrete:
                found.add(f"{model._meta.app_label}.{model.__name__}")
    return found


@pytest.mark.django_db
def test_every_model_referencing_an_account_is_covered_by_the_export():
    """Fails when a later phase adds a model and forgets the export.

    This is the point of enumerating rather than hardcoding: the export must
    stay complete as conversations, tracking and care artefacts arrive.
    """
    missing = models_referencing_account() - set(EXPORTED_MODELS)
    assert not missing, f"models referencing Account but absent from the export: {missing}"


@pytest.mark.django_db
def test_export_contains_the_decrypted_email_and_the_devices(account):
    bound_device(account)
    export = build_export(account)

    assert export["account"]["id"] == str(account.id)
    assert export["identifiers"][0]["value"] == "her@example.com"
    assert len(export["devices"]) == 1


@pytest.mark.django_db
def test_export_never_contains_password_or_token_hashes(account):
    bound_device(account)
    serialised = json.dumps(build_export(account))

    assert account.password not in serialised
    assert Device.objects.get(account=account).token_hash not in serialised


@pytest.mark.django_db
def test_export_endpoint_returns_a_downloadable_attachment(account):
    _, raw = bound_device(account)
    response = Client().post("/api/account/export/", headers={"x-device-token": raw})

    assert response.status_code == 200
    assert "attachment" in response["Content-Disposition"]
    assert json.loads(response.content)["account"]["id"] == str(account.id)


@pytest.mark.django_db
def test_delete_requires_the_password(account):
    _, raw = bound_device(account)
    response = Client().post(
        "/api/account/delete/",
        data={"password": "wrong-password"},
        content_type="application/json",
        headers={"x-device-token": raw},
    )

    assert response.status_code == 400
    assert Account.objects.filter(id=account.id).exists()


@pytest.mark.django_db
def test_delete_leaves_nothing_referencing_the_account(account):
    bound_device(account)
    _, raw = bound_device(account)

    response = Client().post(
        "/api/account/delete/",
        data={"password": PASSWORD},
        content_type="application/json",
        headers={"x-device-token": raw},
    )
    assert response.status_code == 204

    for label in EXPORTED_MODELS:
        model = apps.get_model(label)
        if model is Account:
            assert not model.objects.filter(id=account.id).exists()
            continue
        assert not model.objects.filter(account_id=account.id).exists(), label


@pytest.mark.django_db
def test_the_device_token_stops_working_after_deletion(account):
    _, raw = bound_device(account)
    Client().post(
        "/api/account/delete/",
        data={"password": PASSWORD},
        content_type="application/json",
        headers={"x-device-token": raw},
    )
    assert Client().get("/api/whoami/", headers={"x-device-token": raw}).status_code == 401


@pytest.mark.django_db
def test_an_anonymous_device_cannot_delete_anything():
    raw = generate_device_token()
    Device.objects.create(token_hash=hash_device_token(raw))
    response = Client().post(
        "/api/account/delete/",
        data={"password": PASSWORD},
        content_type="application/json",
        headers={"x-device-token": raw},
    )
    assert response.status_code == 403
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest tests/test_data_rights.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'apps.accounts.data_rights'`

- [ ] **Step 3: Write the module**

Create `backend/apps/accounts/data_rights.py`:

```python
"""Export and deletion.

EXPORTED_MODELS is the list every model touching an Account must appear in.
A test enumerates Django's model registry and fails when something references
Account without being listed here, so the export cannot quietly stop being
complete as later phases add conversations, tracking and care artefacts.
"""

EXPORTED_MODELS = (
    "accounts.Account",
    "accounts.Identifier",
    "accounts.Device",
)


def build_export(account) -> dict:
    """Everything held about this account, in plain JSON-serialisable form.

    Password hashes and device token hashes are excluded deliberately: they are
    credentials rather than her data, and handing them over in a file would put
    her account at risk if the file were read by someone else.
    """
    return {
        "account": {
            "id": str(account.id),
            "created_at": account.created_at.isoformat(),
        },
        "identifiers": [
            {
                "kind": identifier.kind,
                "value": identifier.value,
                "verified_at": (
                    identifier.verified_at.isoformat()
                    if identifier.verified_at
                    else None
                ),
            }
            for identifier in account.identifiers.order_by("created_at")
        ],
        "devices": [
            {
                "id": str(device.id),
                "label": device.label,
                "locale": device.locale,
                "created_at": device.created_at.isoformat(),
                "bound_at": device.bound_at.isoformat() if device.bound_at else None,
                "last_seen": device.last_seen.isoformat(),
            }
            for device in account.devices.order_by("created_at")
        ],
    }
```

- [ ] **Step 4: Add the serializer and views**

Append to `backend/apps/accounts/serializers.py`:

```python
class AccountDeleteSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True)
```

Append to `backend/apps/accounts/account_views.py`:

```python
import json

from django.http import HttpResponse

from apps.accounts.data_rights import build_export
from apps.accounts.serializers import AccountDeleteSerializer


@api_view(["POST"])
def account_export(request):
    account = _require_account(request)
    if account is None:
        return Response(
            {"detail": "This device is not signed in."},
            status=status.HTTP_403_FORBIDDEN,
        )

    # Returned inline rather than written to disk and mailed as a link: no
    # stored artefact to leak, and no link sitting in an inbox someone else
    # may read.
    payload = json.dumps(build_export(account), indent=2)
    response = HttpResponse(payload, content_type="application/json")
    response["Content-Disposition"] = 'attachment; filename="femopedia-export.json"'
    return response


@api_view(["POST"])
def account_delete(request):
    account = _require_account(request)
    if account is None:
        return Response(
            {"detail": "This device is not signed in."},
            status=status.HTTP_403_FORBIDDEN,
        )

    serializer = AccountDeleteSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    # A valid device token is never sufficient: the person holding the
    # unlocked phone may not be her.
    if not account.check_password(serializer.validated_data["password"]):
        return Response(
            {"detail": "Password is incorrect."}, status=status.HTTP_400_BAD_REQUEST
        )

    # Immediate and hard, with no grace period. If she is deleting because
    # someone found this application on her phone, a waiting period leaves the
    # data in place during exactly the window in which it can hurt her.
    account.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)
```

- [ ] **Step 5: Route them**

Add to `urlpatterns`:

```python
    path("account/export/", account_views.account_export, name="account-export"),
    path("account/delete/", account_views.account_delete, name="account-delete"),
```

- [ ] **Step 6: Run the tests to verify they pass**

Run: `uv run pytest tests/test_data_rights.py -v` — all 8 pass.
Run: `uv run pytest -q && uv run ruff check .` — green.
Regenerate the schema.

- [ ] **Step 7: Commit**

```bash
git add backend/ && git commit -m "feat(accounts): export and deletion, complete by enumeration"
```

---

## Definition of done

- A woman can sign up with an email or with a username plus a recovery code, verify her email, sign in on a second device, see both devices, revoke one, change or reset her password, export everything held about her, and delete it all.
- Deleting an account leaves no row in any table referencing it, proved by enumerating Django's model registry rather than by a hardcoded list.
- Anonymous use is unchanged: the whole pre-existing suite passes untouched.
- No plaintext email or username appears in any database column.
- `uv run ruff check .` exits 0 and `schema.yml` matches the generated schema.

## What this plan deliberately does not do

No Google OAuth, no identifier management endpoints, no history merge at signup, no dashboard UI, no app lock, no tracking features. OAuth and identifier management are plan B. History merge belongs to the phase that introduces conversations, and must land before any conversation is written.
