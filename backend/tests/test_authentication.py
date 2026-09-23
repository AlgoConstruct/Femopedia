import pytest
from django.test import Client

from apps.accounts.models import Device
from apps.accounts.tokens import generate_device_token, hash_device_token


@pytest.fixture
def device_with_token(db):
    raw = generate_device_token()
    device = Device.objects.create(token_hash=hash_device_token(raw))
    return device, raw


@pytest.mark.django_db
def test_whoami_returns_the_device_for_a_valid_token(device_with_token):
    device, raw = device_with_token
    response = Client().get("/api/whoami/", headers={"x-device-token": raw})
    assert response.status_code == 200
    assert response.json() == {"device_id": str(device.id)}


@pytest.mark.django_db
def test_whoami_rejects_a_missing_token():
    response = Client().get("/api/whoami/")
    assert response.status_code == 401


@pytest.mark.django_db
def test_whoami_rejects_an_unknown_token():
    response = Client().get("/api/whoami/", headers={"x-device-token": "not-a-real-token"})
    assert response.status_code == 401


@pytest.mark.django_db
def test_authentication_updates_last_seen(device_with_token):
    device, raw = device_with_token
    before = device.last_seen
    Client().get("/api/whoami/", headers={"x-device-token": raw})
    device.refresh_from_db()
    assert device.last_seen > before
