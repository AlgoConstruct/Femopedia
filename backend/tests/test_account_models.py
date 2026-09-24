import pytest

from apps.accounts.models import Account, Device, Identifier
from apps.accounts.tokens import generate_device_token, hash_device_token


@pytest.mark.django_db
def test_password_is_hashed_not_stored():
    account = Account.objects.create()
    account.set_password("a-real-password")
    account.save()

    account.refresh_from_db()
    assert account.password != "a-real-password"
    assert account.check_password("a-real-password") is True
    assert account.check_password("wrong") is False


@pytest.mark.django_db
def test_an_account_with_no_password_and_no_recovery_code_has_no_usable_login():
    account = Account.objects.create()
    assert account.has_usable_login() is False

    account.set_password("a-real-password")
    assert account.has_usable_login() is True


@pytest.mark.django_db
def test_identifier_stores_no_plaintext_and_round_trips():
    account = Account.objects.create()
    identifier = Identifier.create_for(account, Identifier.KIND_EMAIL, "Her@Example.com")

    assert "Her@Example.com" not in identifier.value_encrypted
    assert "her@example.com" not in identifier.value_encrypted
    assert identifier.value == "Her@Example.com"
    assert len(identifier.value_hash) == 64


@pytest.mark.django_db
def test_identifier_lookup_is_case_insensitive():
    account = Account.objects.create()
    Identifier.create_for(account, Identifier.KIND_EMAIL, "her@example.com")

    assert Identifier.lookup(Identifier.KIND_EMAIL, "HER@EXAMPLE.COM").account_id == account.id
    assert Identifier.lookup(Identifier.KIND_EMAIL, "other@example.com") is None


@pytest.mark.django_db
def test_the_same_identifier_cannot_belong_to_two_accounts():
    from django.db import IntegrityError

    first = Account.objects.create()
    second = Account.objects.create()
    Identifier.create_for(first, Identifier.KIND_EMAIL, "her@example.com")

    with pytest.raises(IntegrityError):
        Identifier.create_for(second, Identifier.KIND_EMAIL, "her@example.com")


@pytest.mark.django_db
def test_the_same_value_may_exist_under_different_kinds():
    account = Account.objects.create()
    Identifier.create_for(account, Identifier.KIND_EMAIL, "sameword")
    Identifier.create_for(account, Identifier.KIND_USERNAME, "sameword")
    assert account.identifiers.count() == 2


@pytest.mark.django_db
def test_a_device_is_anonymous_until_bound():
    device = Device.objects.create(token_hash=hash_device_token(generate_device_token()))
    assert device.account_id is None

    account = Account.objects.create()
    device.account = account
    device.save()

    assert account.devices.get().id == device.id


@pytest.mark.django_db
def test_deleting_an_account_deletes_its_devices_and_identifiers():
    account = Account.objects.create()
    Identifier.create_for(account, Identifier.KIND_EMAIL, "her@example.com")
    Device.objects.create(
        token_hash=hash_device_token(generate_device_token()), account=account
    )

    account.delete()

    assert Device.objects.count() == 0
    assert Identifier.objects.count() == 0
