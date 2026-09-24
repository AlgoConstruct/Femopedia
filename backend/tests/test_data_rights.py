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


def _forward_edges():
    """Map each installed model to the concrete related models it points at.

    Only forward, concrete relations are followed (a reverse accessor such as
    Account.devices has field.concrete == False and is excluded), so this
    graph cannot be walked "backwards" into every model that merely has a
    reverse relation somewhere in the app registry.
    """
    return {
        model: {
            field.related_model
            for field in model._meta.get_fields()
            if getattr(field, "related_model", None) and field.concrete
        }
        for model in apps.get_models()
    }


def _reaches_account(model, edges, account_model=Account):
    """True when `model` reaches `account_model` via any chain of forward,
    concrete relations, direct or indirect.

    A depth-first search with a `seen` set, so a cycle in the relation graph
    (e.g. two models pointing at each other) terminates instead of looping.
    """
    stack, seen = list(edges.get(model, ())), set()
    while stack:
        node = stack.pop()
        if node in seen:
            continue
        seen.add(node)
        if node is account_model:
            return True
        stack.extend(edges.get(node, ()))
    return False


def models_referencing_account():
    """Every model that reaches Account via a chain of concrete relations,
    direct or indirect, by dotted label.

    Transitive rather than single-hop: a later phase's Message model, which
    points at Conversation, which points at Device, which points at Account,
    never has a field of its own whose related_model is Account -- a
    single-hop check would miss it, and the export would silently drop
    everything she ever wrote. Walking the whole chain is what makes this
    test able to catch that.
    """
    edges = _forward_edges()
    return {
        f"{model._meta.app_label}.{model.__name__}"
        for model in edges
        if model is not Account and _reaches_account(model, edges)
    }


@pytest.mark.django_db
def test_every_model_referencing_an_account_is_covered_by_the_export():
    """Fails when a later phase adds a model and forgets the export.

    This is the point of enumerating rather than hardcoding: the export must
    stay complete as conversations, tracking and care artefacts arrive.
    """
    missing = models_referencing_account() - set(EXPORTED_MODELS)
    assert not missing, f"models referencing Account but absent from the export: {missing}"


def test_the_walk_finds_a_model_two_hops_from_account():
    """Proves the walk is transitive, not single-hop.

    Stands in for the shape the conversations phase will introduce: Message
    points at Conversation, Conversation points at Device, Device points at
    Account. Leaf here (like Message there) has no field of its own whose
    related_model is Account -- only a single-hop check would miss it.
    """

    class Account:
        pass

    class Middle:
        pass

    class Leaf:
        pass

    edges = {Middle: {Account}, Leaf: {Middle}}

    assert _reaches_account(Leaf, edges, account_model=Account) is True
    assert _reaches_account(Middle, edges, account_model=Account) is True


def test_the_walk_does_not_find_a_model_with_no_path_to_account():
    class Account:
        pass

    class Unrelated:
        pass

    edges = {Unrelated: set()}

    assert _reaches_account(Unrelated, edges, account_model=Account) is False


def test_the_walk_terminates_on_a_cycle():
    """Two models pointing at each other, neither reaching Account, must not
    loop forever."""

    class Account:
        pass

    class A:
        pass

    class B:
        pass

    edges = {A: {B}, B: {A}}

    assert _reaches_account(A, edges, account_model=Account) is False


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

    # Derived from the walk itself, not from EXPORTED_MODELS: the "nothing
    # survives" proof must not be able to silently decouple from the
    # enumeration guarantee again.
    assert not Account.objects.filter(id=account.id).exists()
    for label in models_referencing_account():
        model = apps.get_model(label)
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
