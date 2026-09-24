import uuid
from hashlib import sha256

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
