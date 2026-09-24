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
