import pytest
from django.test import Client

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


def new_device():
    raw = generate_device_token()
    return Device.objects.create(token_hash=hash_device_token(raw)), raw


@pytest.mark.django_db
def test_login_binds_the_calling_device(account):
    device, raw = new_device()
    response = Client().post(
        "/api/auth/login/",
        data={"email": "her@example.com", "password": PASSWORD},
        content_type="application/json",
        headers={"x-device-token": raw},
    )

    assert response.status_code == 200
    device.refresh_from_db()
    assert device.account_id == account.id


@pytest.mark.django_db
def test_a_second_device_reaches_the_same_account(account):
    first, first_raw = new_device()
    second, second_raw = new_device()
    payload = {"email": "her@example.com", "password": PASSWORD}

    for raw in (first_raw, second_raw):
        Client().post(
            "/api/auth/login/",
            data=payload,
            content_type="application/json",
            headers={"x-device-token": raw},
        )

    first.refresh_from_db()
    second.refresh_from_db()
    assert first.account_id == second.account_id == account.id


@pytest.mark.django_db
def test_a_wrong_password_is_rejected_and_binds_nothing(account):
    device, raw = new_device()
    response = Client().post(
        "/api/auth/login/",
        data={"email": "her@example.com", "password": "wrong-password"},
        content_type="application/json",
        headers={"x-device-token": raw},
    )

    assert response.status_code == 401
    device.refresh_from_db()
    assert device.account_id is None


@pytest.mark.django_db
def test_an_unknown_email_answers_exactly_like_a_wrong_password(account):
    _device, raw = new_device()
    unknown = Client().post(
        "/api/auth/login/",
        data={"email": "nobody@example.com", "password": PASSWORD},
        content_type="application/json",
        headers={"x-device-token": raw},
    )
    wrong = Client().post(
        "/api/auth/login/",
        data={"email": "her@example.com", "password": "wrong-password"},
        content_type="application/json",
        headers={"x-device-token": raw},
    )

    # Differing answers would tell anyone who asks whether a given woman has
    # an account here.
    assert unknown.status_code == wrong.status_code == 401
    assert unknown.json() == wrong.json()


@pytest.mark.django_db
def test_logout_issues_a_fresh_anonymous_token_and_destroys_the_old_device(account):
    device, raw = new_device()
    Client().post(
        "/api/auth/login/",
        data={"email": "her@example.com", "password": PASSWORD},
        content_type="application/json",
        headers={"x-device-token": raw},
    )

    response = Client().post("/api/auth/logout/", headers={"x-device-token": raw})
    assert response.status_code == 200

    new_token = response.json()["device_token"]
    assert new_token != raw
    assert not Device.objects.filter(id=device.id).exists()

    fresh = Device.objects.get(token_hash=hash_device_token(new_token))
    assert fresh.account_id is None


@pytest.mark.django_db
def test_the_old_token_stops_working_after_logout(account):
    _, raw = new_device()
    Client().post(
        "/api/auth/login/",
        data={"email": "her@example.com", "password": PASSWORD},
        content_type="application/json",
        headers={"x-device-token": raw},
    )
    Client().post("/api/auth/logout/", headers={"x-device-token": raw})

    assert Client().get("/api/whoami/", headers={"x-device-token": raw}).status_code == 401
