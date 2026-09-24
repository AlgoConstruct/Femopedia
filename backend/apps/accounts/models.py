import uuid

from django.db import models

SUPPORTED_LOCALES = ("ne", "ne-Latn", "hi-Latn", "en")


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
    last_seen = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "accounts_device"

    @property
    def is_authenticated(self) -> bool:
        """DRF permission classes check this attribute on request.user."""
        return True

    def __str__(self) -> str:
        return f"Device {self.id}"
