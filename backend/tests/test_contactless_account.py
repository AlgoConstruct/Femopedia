from unittest import mock

import pytest
from django.db import IntegrityError
from django.test import Client

from apps.accounts.models import Account, Device, Identifier
from apps.accounts.tokens import (
    generate_device_token,
    generate_recovery_code,
    hash_device_token,
    hash_recovery_code,
)


def new_device():
    raw = generate_device_token()
    return Device.objects.create(token_hash=hash_device_token(raw)), raw


def bound_device(account):
    raw = generate_device_token()
    return Device.objects.create(token_hash=hash_device_token(raw), account=account), raw


def test_recovery_codes_are_unique_and_grouped():
    codes = {generate_recovery_code() for _ in range(200)}
    assert len(codes) == 200
    sample = generate_recovery_code()
    assert len(sample.split("-")) == 6
    assert sample == sample.upper()


def test_recovery_code_hash_ignores_case_and_spacing():
    code = "ABCD-EFGH-IJKL-MNOP-QRST-UVWX"
    assert hash_recovery_code(code) == hash_recovery_code(" abcd-efgh-ijkl-mnop-qrst-uvwx ")
    assert len(hash_recovery_code(code)) == 64


@pytest.mark.django_db
def test_username_signup_returns_the_recovery_code_exactly_once():
    _, raw = new_device()
    response = Client().post(
        "/api/auth/signup/",
        data={"username": "sunita", "password": "a-real-password"},
        content_type="application/json",
        headers={"x-device-token": raw},
    )

    assert response.status_code == 201
    body = response.json()
    assert set(body) == {"account_id", "recovery_code"}

    account = Account.objects.get(id=body["account_id"])
    assert account.recovery_code_hash == hash_recovery_code(body["recovery_code"])
    assert body["recovery_code"] not in account.recovery_code_hash


@pytest.mark.django_db
def test_username_signup_stores_no_email_identifier():
    _, raw = new_device()
    Client().post(
        "/api/auth/signup/",
        data={"username": "sunita", "password": "a-real-password"},
        content_type="application/json",
        headers={"x-device-token": raw},
    )
    assert Identifier.objects.filter(kind=Identifier.KIND_EMAIL).count() == 0
    assert Identifier.objects.filter(kind=Identifier.KIND_USERNAME).count() == 1


@pytest.mark.django_db
def test_signup_rejects_a_payload_with_neither_email_nor_username():
    _, raw = new_device()
    response = Client().post(
        "/api/auth/signup/",
        data={"password": "a-real-password"},
        content_type="application/json",
        headers={"x-device-token": raw},
    )
    assert response.status_code == 400
    assert Account.objects.count() == 0


@pytest.mark.django_db
def test_signup_returns_the_vague_duplicate_username_error_on_a_database_race():
    """Modelled on test_signup_email.py's
    test_signup_returns_the_vague_duplicate_email_error_on_a_database_race:
    two concurrent username signups can both pass
    UsernameSignupSerializer.validate_username before either commits; the
    loser must hit the database's unique constraint on (kind, value_hash)
    and still read as an ordinary duplicate-username 400 -- not a 500, and
    not the email-shaped error that names a field never in this request."""
    _, raw = new_device()
    with mock.patch(
        "apps.accounts.auth_views.Identifier.create_for",
        side_effect=IntegrityError("duplicate key value violates unique constraint"),
    ):
        response = Client().post(
            "/api/auth/signup/",
            data={"username": "sunita", "password": "a-real-password"},
            content_type="application/json",
            headers={"x-device-token": raw},
        )

    assert response.status_code == 400
    assert response.json() == {"username": ["This username cannot be used."]}
    assert Account.objects.count() == 0


@pytest.mark.django_db
def test_recovery_sets_a_new_password_and_replaces_the_code():
    _, raw = new_device()
    signup = Client().post(
        "/api/auth/signup/",
        data={"username": "sunita", "password": "a-real-password"},
        content_type="application/json",
        headers={"x-device-token": raw},
    ).json()

    response = Client().post(
        "/api/auth/recover/",
        data={
            "username": "sunita",
            "recovery_code": signup["recovery_code"],
            "new_password": "a-brand-new-password",
        },
        content_type="application/json",
    )

    assert response.status_code == 200
    replacement = response.json()["recovery_code"]
    assert replacement != signup["recovery_code"]

    account = Account.objects.get(id=signup["account_id"])
    assert account.check_password("a-brand-new-password") is True
    assert account.recovery_code_hash == hash_recovery_code(replacement)


@pytest.mark.django_db
def test_a_used_recovery_code_cannot_be_used_again():
    _, raw = new_device()
    signup = Client().post(
        "/api/auth/signup/",
        data={"username": "sunita", "password": "a-real-password"},
        content_type="application/json",
        headers={"x-device-token": raw},
    ).json()

    payload = {
        "username": "sunita",
        "recovery_code": signup["recovery_code"],
        "new_password": "a-brand-new-password",
    }
    Client().post("/api/auth/recover/", data=payload, content_type="application/json")
    second = Client().post(
        "/api/auth/recover/", data=payload, content_type="application/json"
    )

    assert second.status_code == 400


@pytest.mark.django_db
def test_recovery_answers_identically_for_an_unknown_username():
    unknown = Client().post(
        "/api/auth/recover/",
        data={
            "username": "nobody",
            "recovery_code": "ABCD-EFGH-IJKL-MNOP-QRST-UVWX",
            "new_password": "a-brand-new-password",
        },
        content_type="application/json",
    )
    assert unknown.status_code == 400


@pytest.mark.django_db
def test_recovery_hashes_the_supplied_code_even_for_an_unknown_username():
    """C3: the miss path (unknown username) used to return before
    hash_recovery_code ran at all, skipping the one piece of work the real
    lookup-then-compare path always does. hash_recovery_code is SHA-256, so
    the gap this closes is far smaller than login's PBKDF2 case, but the
    shape should not skip work an attacker could measure."""
    with mock.patch(
        "apps.accounts.auth_views.hash_recovery_code", wraps=hash_recovery_code
    ) as wrapped:
        Client().post(
            "/api/auth/recover/",
            data={
                "username": "nobody",
                "recovery_code": "ABCD-EFGH-IJKL-MNOP-QRST-UVWX",
                "new_password": "a-brand-new-password",
            },
            content_type="application/json",
        )
    wrapped.assert_called_once()


@pytest.mark.django_db
def test_recovery_revokes_every_other_device_but_not_the_callers():
    """I3: she reaches for recovery because she believes someone else has
    access; a recovery that leaves their session alive elsewhere does not
    help her. The caller's own device -- not necessarily bound to this
    account yet, since recover() never binds one -- is spared regardless."""
    _, raw = new_device()
    signup = Client().post(
        "/api/auth/signup/",
        data={"username": "sunita", "password": "a-real-password"},
        content_type="application/json",
        headers={"x-device-token": raw},
    ).json()
    account = Account.objects.get(id=signup["account_id"])

    caller_device, caller_raw = bound_device(account)
    other_device, other_raw = bound_device(account)

    response = Client().post(
        "/api/auth/recover/",
        data={
            "username": "sunita",
            "recovery_code": signup["recovery_code"],
            "new_password": "a-brand-new-password",
        },
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
    assert not Device.objects.filter(id=other_device.id).exists()
    assert Device.objects.filter(id=caller_device.id).exists()
