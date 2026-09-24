import pytest
from django.test import Client

from apps.accounts.models import Account, Device, Identifier
from apps.accounts.tokens import generate_device_token, hash_device_token


@pytest.fixture
def account(db):
    account = Account.objects.create()
    account.set_password("a-real-password")
    account.save()
    Identifier.create_for(account, Identifier.KIND_EMAIL, "her@example.com", verified=True)
    return account


def bound_device(account, label=""):
    raw = generate_device_token()
    device = Device.objects.create(
        token_hash=hash_device_token(raw), account=account, label=label
    )
    return device, raw


@pytest.mark.django_db
def test_account_summary_names_identifier_kinds_but_never_their_values(account):
    _, raw = bound_device(account)
    response = Client().get("/api/account/", headers={"x-device-token": raw})

    assert response.status_code == 200
    body = response.json()
    assert body["account_id"] == str(account.id)
    assert body["identifiers"] == [{"kind": "email", "verified": True}]
    assert "her@example.com" not in response.content.decode()


@pytest.mark.django_db
def test_device_list_shows_every_bound_device_and_marks_the_caller(account):
    first, first_raw = bound_device(account, label="Phone")
    second, _ = bound_device(account, label="Laptop")

    response = Client().get("/api/account/devices/", headers={"x-device-token": first_raw})
    devices = {d["id"]: d for d in response.json()["devices"]}

    assert set(devices) == {str(first.id), str(second.id)}
    assert devices[str(first.id)]["is_current"] is True
    assert devices[str(second.id)]["is_current"] is False


@pytest.mark.django_db
def test_device_list_never_exposes_a_token_hash(account):
    _, raw = bound_device(account)
    response = Client().get("/api/account/devices/", headers={"x-device-token": raw})
    device = Device.objects.get(account=account)
    assert device.token_hash not in response.content.decode()


@pytest.mark.django_db
def test_revoking_another_device_deletes_it(account):
    _, raw = bound_device(account)
    other, other_raw = bound_device(account)

    response = Client().delete(
        f"/api/account/devices/{other.id}/", headers={"x-device-token": raw}
    )

    assert response.status_code == 204
    assert not Device.objects.filter(id=other.id).exists()
    assert Client().get("/api/whoami/", headers={"x-device-token": other_raw}).status_code == 401


@pytest.mark.django_db
def test_a_device_belonging_to_another_account_cannot_be_revoked(account):
    _, raw = bound_device(account)

    stranger = Account.objects.create()
    their_device, _ = bound_device(stranger)

    response = Client().delete(
        f"/api/account/devices/{their_device.id}/", headers={"x-device-token": raw}
    )

    assert response.status_code == 404
    assert Device.objects.filter(id=their_device.id).exists()


@pytest.mark.django_db
def test_an_anonymous_device_has_no_account_endpoints():
    raw = generate_device_token()
    Device.objects.create(token_hash=hash_device_token(raw))
    assert Client().get("/api/account/", headers={"x-device-token": raw}).status_code == 403


@pytest.mark.django_db
def test_an_anonymous_device_cannot_list_devices():
    raw = generate_device_token()
    Device.objects.create(token_hash=hash_device_token(raw))
    response = Client().get("/api/account/devices/", headers={"x-device-token": raw})
    assert response.status_code == 403


@pytest.mark.django_db
def test_an_anonymous_device_cannot_revoke_a_device():
    raw = generate_device_token()
    Device.objects.create(token_hash=hash_device_token(raw))

    account = Account.objects.create()
    other, _ = bound_device(account)

    response = Client().delete(
        f"/api/account/devices/{other.id}/", headers={"x-device-token": raw}
    )
    assert response.status_code == 403


@pytest.mark.django_db
def test_authentication_records_a_device_label(account):
    _, raw = bound_device(account)
    Client().get(
        "/api/whoami/",
        headers={"x-device-token": raw, "user-agent": "Mozilla/5.0 (Linux; Android 14)"},
    )
    device = Device.objects.get(account=account)
    assert "Android" in device.label
