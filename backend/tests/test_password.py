from unittest import mock

import pytest
from django.core import mail
from django.core.signing import SignatureExpired, TimestampSigner
from django.test import Client

from apps.accounts import verification
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

    # I9: the first (successful) confirm already changed the password to
    # "a-brand-new-password" -- the point of this test is that the *second*,
    # rejected attempt leaves it exactly there, neither reverting it nor
    # applying a second change.
    account.refresh_from_db()
    assert account.check_password("a-brand-new-password") is True


@pytest.mark.django_db
def test_a_reset_token_minted_for_one_account_is_rejected_for_another(account):
    """I9: forging a token for a different account by re-signing the
    payload with someone else's id must fail -- the fingerprint is a hash of
    the *original* account's password, so it will not match the target
    account's, even though the signature itself is otherwise valid."""
    other = Account.objects.create()
    other.set_password("some-other-password")
    other.save()

    token = verification.make_reset_token(account)
    _account_id, fingerprint = verification.read_reset_token(token)
    forged = TimestampSigner(salt=verification.RESET_SALT).sign(f"{other.id}:{fingerprint}")

    response = Client().post(
        "/api/auth/password-reset/confirm/",
        data={"token": forged, "new_password": "a-brand-new-password"},
        content_type="application/json",
    )

    assert response.status_code == 400
    other.refresh_from_db()
    assert other.check_password("a-brand-new-password") is False


@pytest.mark.django_db
def test_reset_confirm_rejects_a_tampered_or_garbage_token(account):
    """I9."""
    response = Client().post(
        "/api/auth/password-reset/confirm/",
        data={"token": "not-a-real-token", "new_password": "a-brand-new-password"},
        content_type="application/json",
    )

    assert response.status_code == 400
    account.refresh_from_db()
    assert account.check_password(PASSWORD) is True


@pytest.mark.django_db
def test_an_expired_reset_token_is_rejected(account):
    """I9: mirrors test_email_verification.py's
    test_an_expired_token_is_rejected -- the verification token had this
    test, the reset token did not."""
    token = verification.make_reset_token(account)
    with pytest.raises(SignatureExpired):
        verification.read_reset_token(token, max_age_seconds=-1)


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
def test_a_known_but_unverified_address_answers_byte_identically_to_an_unknown_one():
    """I9: status codes and .json() equality (already asserted above for the
    known-verified vs unknown case) can hide a body that differs in key
    order or whitespace. This compares raw response bytes for the
    known-but-unverified case specifically, since that is the one that
    shares "no mail sent" with the unknown case and so is the easiest of the
    three to accidentally answer differently."""
    account = Account.objects.create()
    account.set_password(PASSWORD)
    account.save()
    Identifier.create_for(account, Identifier.KIND_EMAIL, "unverified@example.com")

    known_unverified = Client().post(
        "/api/auth/password-reset/",
        data={"email": "unverified@example.com"},
        content_type="application/json",
    )
    unknown = Client().post(
        "/api/auth/password-reset/",
        data={"email": "nobody-at-all@example.com"},
        content_type="application/json",
    )

    assert known_unverified.status_code == unknown.status_code == 202
    assert known_unverified.content == unknown.content


@pytest.mark.django_db
def test_reset_request_still_returns_202_when_the_mail_backend_raises(account):
    """C2: without the broad try/except around the send, an SMTP outage
    would answer a known-and-verified address with a 500 while every other
    case still answers 202 -- an outage-shaped version of exactly the oracle
    this endpoint exists to avoid."""
    with mock.patch(
        "apps.accounts.auth_views.verification.send_password_reset_email",
        side_effect=RuntimeError("smtp is down"),
    ):
        response = Client().post(
            "/api/auth/password-reset/",
            data={"email": "her@example.com"},
            content_type="application/json",
        )

    assert response.status_code == 202
    assert response.json() == {"status": "sent"}


@pytest.mark.django_db
def test_reset_confirm_revokes_every_other_device_but_not_the_callers(account):
    """I3: she reaches for password reset because she believes someone else
    has access; a reset that leaves their session alive elsewhere does not
    help her."""
    caller_raw = bound_device(account)
    other_raw = bound_device(account)

    token = verification.make_reset_token(account)
    response = Client().post(
        "/api/auth/password-reset/confirm/",
        data={"token": token, "new_password": "a-brand-new-password"},
        content_type="application/json",
        headers={"x-device-token": caller_raw},
    )

    assert response.status_code == 200
    assert (
        Client().get("/api/whoami/", headers={"x-device-token": other_raw}).status_code
        == 401
    )
    assert (
        Client().get("/api/whoami/", headers={"x-device-token": caller_raw}).status_code
        == 200
    )


@pytest.mark.django_db
def test_password_change_revokes_every_other_device_but_not_the_callers(account):
    """I3, applied to password_change for consistency with reset and recover."""
    caller_raw = bound_device(account)
    other_raw = bound_device(account)

    response = Client().post(
        "/api/account/password/",
        data={"current_password": PASSWORD, "new_password": "a-brand-new-password"},
        content_type="application/json",
        headers={"x-device-token": caller_raw},
    )

    assert response.status_code == 200
    assert (
        Client().get("/api/whoami/", headers={"x-device-token": other_raw}).status_code
        == 401
    )
    assert (
        Client().get("/api/whoami/", headers={"x-device-token": caller_raw}).status_code
        == 200
    )


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
