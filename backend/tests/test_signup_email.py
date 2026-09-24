import sys
from unittest import mock

import pytest
from django.db import IntegrityError
from django.test import Client, RequestFactory, override_settings

from apps.accounts import auth_views
from apps.accounts.models import Account, Device, Identifier
from apps.accounts.tokens import generate_device_token, hash_device_token
from tests.test_sensitive_variables import _cleansed_locals_for_frame


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


@pytest.mark.django_db
def test_signup_cleanses_the_password_from_its_frame_locals(device):
    """Modelled on tests/test_sensitive_variables.py's coverage of the
    analogous secret (the raw device token) in create_device and
    DeviceTokenAuthentication.authenticate: force an unhandled exception
    inside signup and confirm the password local is scrubbed from the
    traceback frame Django's error reporting would otherwise mail out in
    cleartext."""
    _, raw = device
    request = RequestFactory().post(
        "/api/auth/signup/",
        data={"email": "her@example.com", "password": "a-real-password"},
        content_type="application/json",
        HTTP_X_DEVICE_TOKEN=raw,
    )

    with (
        mock.patch(
            "apps.accounts.auth_views.Account.save",
            side_effect=RuntimeError("db exploded"),
        ),
        override_settings(DEBUG=False),
    ):
        try:
            auth_views.signup(request)
        except RuntimeError:
            cleansed = _cleansed_locals_for_frame("signup", sys.exc_info()[2])
        else:
            raise AssertionError("signup() was expected to raise when Account.save fails")

    assert cleansed["password"] == "********************"


@pytest.mark.django_db
def test_signup_returns_the_vague_duplicate_email_error_on_a_database_race(device):
    """Two concurrent signups for the same address can both pass the
    serializer's own duplicate-email check before either commits; the loser
    must hit the database's unique constraint on (kind, value_hash) and
    still read as an ordinary duplicate-email 400 -- not a 500, and not a
    louder error than the vague one the serializer already uses."""
    _, raw = device
    with mock.patch(
        "apps.accounts.auth_views.Identifier.create_for",
        side_effect=IntegrityError("duplicate key value violates unique constraint"),
    ):
        response = Client().post(
            "/api/auth/signup/",
            data={"email": "her@example.com", "password": "a-real-password"},
            content_type="application/json",
            headers={"x-device-token": raw},
        )

    assert response.status_code == 400
    assert response.json() == {"email": ["This email cannot be used."]}
    assert Account.objects.count() == 0
