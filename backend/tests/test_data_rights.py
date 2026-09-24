import json

import pytest
from django.apps import apps
from django.test import Client

from apps.accounts.data_rights import EXPORTED_MODELS, build_export
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
    return Device.objects.create(token_hash=hash_device_token(raw), account=account), raw


def models_referencing_account():
    """Every model with a relation to Account, by dotted label."""
    found = set()
    for model in apps.get_models():
        for field in model._meta.get_fields():
            related = getattr(field, "related_model", None)
            if related is Account and field.concrete:
                found.add(f"{model._meta.app_label}.{model.__name__}")
    return found


@pytest.mark.django_db
def test_every_model_referencing_an_account_is_covered_by_the_export():
    """Fails when a later phase adds a model and forgets the export.

    This is the point of enumerating rather than hardcoding: the export must
    stay complete as conversations, tracking and care artefacts arrive.
    """
    missing = models_referencing_account() - set(EXPORTED_MODELS)
    assert not missing, f"models referencing Account but absent from the export: {missing}"


@pytest.mark.django_db
def test_export_contains_the_decrypted_email_and_the_devices(account):
    bound_device(account)
    export = build_export(account)

    assert export["account"]["id"] == str(account.id)
    assert export["identifiers"][0]["value"] == "her@example.com"
    assert len(export["devices"]) == 1


@pytest.mark.django_db
def test_export_never_contains_password_or_token_hashes(account):
    bound_device(account)
    serialised = json.dumps(build_export(account))

    assert account.password not in serialised
    assert Device.objects.get(account=account).token_hash not in serialised


@pytest.mark.django_db
def test_export_endpoint_returns_a_downloadable_attachment(account):
    _, raw = bound_device(account)
    response = Client().post("/api/account/export/", headers={"x-device-token": raw})

    assert response.status_code == 200
    assert "attachment" in response["Content-Disposition"]
    assert json.loads(response.content)["account"]["id"] == str(account.id)


@pytest.mark.django_db
def test_delete_requires_the_password(account):
    _, raw = bound_device(account)
    response = Client().post(
        "/api/account/delete/",
        data={"password": "wrong-password"},
        content_type="application/json",
        headers={"x-device-token": raw},
    )

    assert response.status_code == 400
    assert Account.objects.filter(id=account.id).exists()


@pytest.mark.django_db
def test_delete_leaves_nothing_referencing_the_account(account):
    bound_device(account)
    _, raw = bound_device(account)

    response = Client().post(
        "/api/account/delete/",
        data={"password": PASSWORD},
        content_type="application/json",
        headers={"x-device-token": raw},
    )
    assert response.status_code == 204

    for label in EXPORTED_MODELS:
        model = apps.get_model(label)
        if model is Account:
            assert not model.objects.filter(id=account.id).exists()
            continue
        assert not model.objects.filter(account_id=account.id).exists(), label


@pytest.mark.django_db
def test_the_device_token_stops_working_after_deletion(account):
    _, raw = bound_device(account)
    Client().post(
        "/api/account/delete/",
        data={"password": PASSWORD},
        content_type="application/json",
        headers={"x-device-token": raw},
    )
    assert Client().get("/api/whoami/", headers={"x-device-token": raw}).status_code == 401


@pytest.mark.django_db
def test_an_anonymous_device_cannot_delete_anything():
    raw = generate_device_token()
    Device.objects.create(token_hash=hash_device_token(raw))
    response = Client().post(
        "/api/account/delete/",
        data={"password": PASSWORD},
        content_type="application/json",
        headers={"x-device-token": raw},
    )
    assert response.status_code == 403
