import sys
from unittest import mock

import pytest
from django.test import Client, RequestFactory, override_settings

from apps.accounts import session_views
from apps.accounts.models import Account, Device, Identifier
from apps.accounts.tokens import generate_device_token, hash_device_token
from tests.test_sensitive_variables import _cleansed_locals_for_frame

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
def test_an_unknown_email_still_exercises_the_password_hasher(account):
    """C3: closes the timing gap between "no such account" (~5ms) and "wrong
    password" (~250ms+, the cost of running PBKDF2) that returning before
    ever calling the hasher would otherwise create. Timing itself is not
    asserted here -- timing assertions are flaky -- this asserts the
    mechanism that closes the gap actually runs: the hasher is invoked
    against the dummy hash on the miss path too."""
    _device, raw = new_device()

    with mock.patch(
        "apps.accounts.session_views.django_check_password", wraps=lambda *a, **k: False
    ) as wrapped:
        response = Client().post(
            "/api/auth/login/",
            data={"email": "nobody@example.com", "password": PASSWORD},
            content_type="application/json",
            headers={"x-device-token": raw},
        )

    assert response.status_code == 401
    wrapped.assert_called_once()


@pytest.mark.django_db
def test_login_rebinds_a_device_already_signed_in_to_a_different_account(account):
    """I8: signing in as one woman on a device already signed in as another
    must never silently transfer the device (and her history) between
    accounts -- central given two women sharing a handset. Instead this is a
    logout-then-login: the old device row is destroyed and a brand-new one,
    bound to the newly-authenticated account, is returned."""
    other = Account.objects.create()
    other.set_password("a-different-password")
    other.save()
    Identifier.create_for(other, Identifier.KIND_EMAIL, "other@example.com", verified=True)

    old_device, raw = new_device()
    old_device.account = other
    old_device.bound_at = old_device.created_at
    old_device.save(update_fields=["account", "bound_at"])

    response = Client().post(
        "/api/auth/login/",
        data={"email": "her@example.com", "password": PASSWORD},
        content_type="application/json",
        headers={"x-device-token": raw},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["account_id"] == str(account.id)
    new_token = body["device_token"]
    assert new_token != raw

    assert not Device.objects.filter(id=old_device.id).exists()
    new_device_row = Device.objects.get(token_hash=hash_device_token(new_token))
    assert new_device_row.account_id == account.id

    # The old token is dead; the new one works.
    assert Client().get("/api/whoami/", headers={"x-device-token": raw}).status_code == 401
    assert (
        Client().get("/api/whoami/", headers={"x-device-token": new_token}).status_code
        == 200
    )


@pytest.mark.django_db
def test_login_rebinds_even_when_already_signed_in_to_the_same_account(account):
    """I8's rule is unconditional on device.account_id being set at all, not
    only on it differing from the account being logged into -- a
    logout-then-login either way, never an in-place mutation."""
    old_device, raw = new_device()
    old_device.account = account
    old_device.bound_at = old_device.created_at
    old_device.save(update_fields=["account", "bound_at"])

    response = Client().post(
        "/api/auth/login/",
        data={"email": "her@example.com", "password": PASSWORD},
        content_type="application/json",
        headers={"x-device-token": raw},
    )

    assert response.status_code == 200
    body = response.json()
    new_token = body["device_token"]

    assert not Device.objects.filter(id=old_device.id).exists()
    assert Device.objects.get(token_hash=hash_device_token(new_token)).account_id == account.id


@pytest.mark.django_db
def test_login_cleanses_the_password_from_its_frame_locals(account):
    """Modelled on test_signup_email.py's
    test_signup_cleanses_the_password_from_its_frame_locals: force an
    unhandled exception inside login and confirm the password local is
    scrubbed from the traceback frame Django's error reporting would
    otherwise mail out in cleartext. This also proves
    @sensitive_variables("password") on login now scrubs something --
    previously the decorator named a variable that was never bound to a
    bare local, so it silently protected nothing."""
    _device, raw = new_device()
    request = RequestFactory().post(
        "/api/auth/login/",
        data={"email": "her@example.com", "password": PASSWORD},
        content_type="application/json",
        HTTP_X_DEVICE_TOKEN=raw,
    )

    with (
        mock.patch(
            "apps.accounts.session_views.Identifier.lookup",
            side_effect=RuntimeError("db exploded"),
        ),
        override_settings(DEBUG=False),
    ):
        try:
            session_views.login(request)
        except RuntimeError:
            cleansed = _cleansed_locals_for_frame("login", sys.exc_info()[2])
        else:
            raise AssertionError("login() was expected to raise when Identifier.lookup fails")

    assert cleansed["password"] == "********************"


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
