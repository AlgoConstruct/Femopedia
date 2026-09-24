import hashlib
import secrets


def generate_device_token() -> str:
    """Return a fresh URL-safe device token. Shown to the client exactly once."""
    return secrets.token_urlsafe(32)


def hash_device_token(raw: str) -> str:
    """Return the lowercase SHA-256 hex digest stored in place of the raw token."""
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


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
