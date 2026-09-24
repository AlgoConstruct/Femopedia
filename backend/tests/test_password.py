import pytest
from django.core import mail
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
