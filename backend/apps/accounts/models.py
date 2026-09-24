import uuid

from django.contrib.auth.hashers import check_password as django_check_password
from django.contrib.auth.hashers import make_password
from django.db import models
from django.utils import timezone

from apps.accounts import crypto

SUPPORTED_LOCALES = ("ne", "ne-Latn", "hi-Latn", "en")


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
    KINDS = (
        (KIND_EMAIL, "Email"),
        (KIND_USERNAME, "Username"),
        (KIND_GOOGLE, "Google"),
    )

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
        constraints = (
            models.UniqueConstraint(
                fields=["kind", "value_hash"], name="unique_identifier_per_kind"
            ),
        )

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


class Device(models.Model):
    """An anonymous client. The only credential Femopedia requires."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    token_hash = models.CharField(max_length=64, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    locale = models.CharField(
        max_length=16,
        default="ne",
        choices=[(code, code) for code in SUPPORTED_LOCALES],
    )
    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="devices",
    )
    bound_at = models.DateTimeField(null=True, blank=True)
    label = models.CharField(max_length=120, blank=True, default="")
    last_seen = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "accounts_device"

    @property
    def is_authenticated(self) -> bool:
        """DRF permission classes check this attribute on request.user."""
        return True

    def __str__(self) -> str:
        return f"Device {self.id}"
