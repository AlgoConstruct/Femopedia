import pytest
from django.test import Client

from apps.accounts.models import SUPPORTED_LOCALES, Device
from apps.accounts.tokens import generate_device_token, hash_device_token


def test_generated_tokens_are_unique_and_long():
    tokens = {generate_device_token() for _ in range(100)}
    assert len(tokens) == 100
    assert all(len(t) >= 43 for t in tokens)


def test_hash_is_stable_sha256_hex():
    digest = hash_device_token("abc")
    assert digest == hash_device_token("abc")
    assert len(digest) == 64
    assert digest == digest.lower()
    assert digest != hash_device_token("abd")


@pytest.mark.django_db
def test_create_device_returns_token_once_and_stores_only_the_hash():
    client = Client()
    response = client.post("/api/devices/")

    assert response.status_code == 201
    body = response.json()
    assert set(body) == {"device_id", "device_token"}

    device = Device.objects.get(id=body["device_id"])
    assert device.token_hash == hash_device_token(body["device_token"])
    assert body["device_token"] not in device.token_hash


@pytest.mark.django_db
def test_device_is_authenticated_property():
    device = Device.objects.create(token_hash=hash_device_token("x"))
    assert device.is_authenticated is True


@pytest.mark.django_db
def test_create_device_with_non_dict_json_body_falls_back_to_default_locale():
    client = Client()
    response = client.post("/api/devices/", data=[1, 2, 3], content_type="application/json")

    assert response.status_code == 201
    body = response.json()
    device = Device.objects.get(id=body["device_id"])
    assert device.locale == "ne"


@pytest.mark.django_db
def test_create_device_with_absent_locale_defaults_to_ne():
    client = Client()
    response = client.post("/api/devices/", data={}, content_type="application/json")

    assert response.status_code == 201
    body = response.json()
    device = Device.objects.get(id=body["device_id"])
    assert device.locale == "ne"


@pytest.mark.django_db
def test_create_device_rejects_an_oversized_locale():
    client = Client()
    response = client.post(
        "/api/devices/",
        data={"locale": "a" * 17},
        content_type="application/json",
    )

    assert response.status_code == 400
    assert "detail" in response.json()
    assert not Device.objects.exists()


@pytest.mark.django_db
def test_create_device_rejects_a_non_string_locale():
    client = Client()
    response = client.post(
        "/api/devices/",
        data={"locale": {"a": 1}},
        content_type="application/json",
    )

    assert response.status_code == 400
    assert "detail" in response.json()
    assert not Device.objects.exists()


@pytest.mark.django_db
def test_create_device_rejects_an_unsupported_locale_code():
    client = Client()
    response = client.post(
        "/api/devices/",
        data={"locale": "fr"},
        content_type="application/json",
    )

    assert response.status_code == 400
    assert "detail" in response.json()
    assert not Device.objects.exists()


@pytest.mark.django_db
@pytest.mark.parametrize("locale", SUPPORTED_LOCALES)
def test_create_device_accepts_each_supported_locale(locale):
    client = Client()
    response = client.post(
        "/api/devices/",
        data={"locale": locale},
        content_type="application/json",
    )

    assert response.status_code == 201
    body = response.json()
    device = Device.objects.get(id=body["device_id"])
    assert device.locale == locale
