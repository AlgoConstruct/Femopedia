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
    _row, raw = device
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
