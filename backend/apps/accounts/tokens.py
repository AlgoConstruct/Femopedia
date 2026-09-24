import hashlib
import secrets


def generate_device_token() -> str:
    """Return a fresh URL-safe device token. Shown to the client exactly once."""
    return secrets.token_urlsafe(32)


def hash_device_token(raw: str) -> str:
    """Return the lowercase SHA-256 hex digest stored in place of the raw token."""
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()
