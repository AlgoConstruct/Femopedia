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
