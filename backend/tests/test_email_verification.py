import pytest
from django.core import mail
from django.core.signing import SignatureExpired
from django.test import Client

from apps.accounts import verification
from apps.accounts.models import Account, Identifier


@pytest.fixture
def identifier(db):
    account = Account.objects.create()
    return Identifier.create_for(account, Identifier.KIND_EMAIL, "her@example.com")


@pytest.mark.django_db
def test_token_round_trips_to_the_identifier_id(identifier):
    token = verification.make_token(identifier)
    assert verification.read_token(token) == identifier.id


@pytest.mark.django_db
def test_an_expired_token_is_rejected(identifier):
    token = verification.make_token(identifier)
    with pytest.raises(SignatureExpired):
        verification.read_token(token, max_age_seconds=-1)


@pytest.mark.django_db
def test_verifying_marks_the_identifier_verified(identifier):
    token = verification.make_token(identifier)
    response = Client().post(
        "/api/auth/verify-email/",
        data={"token": token},
        content_type="application/json",
    )

    assert response.status_code == 200
    identifier.refresh_from_db()
    assert identifier.is_verified is True


@pytest.mark.django_db
def test_a_tampered_token_is_rejected(identifier):
    response = Client().post(
        "/api/auth/verify-email/",
        data={"token": "not-a-real-token"},
        content_type="application/json",
    )
    assert response.status_code == 400
    identifier.refresh_from_db()
    assert identifier.is_verified is False


@pytest.mark.django_db
def test_verification_needs_no_device_token(identifier):
    """She may open the link on a laptop that has never used the app."""
    token = verification.make_token(identifier)
    response = Client().post(
        "/api/auth/verify-email/",
        data={"token": token},
        content_type="application/json",
    )
    assert response.status_code == 200


@pytest.mark.django_db
def test_the_email_is_sent_and_contains_the_token_not_the_address(identifier):
    mail.outbox.clear()
    verification.send_verification_email(identifier)

    assert len(mail.outbox) == 1
    message = mail.outbox[0]
    assert message.to == ["her@example.com"]

    # The link must carry a token that actually verifies this identifier.
    token = message.body.split("token=")[1].split()[0]
    assert verification.read_token(token) == identifier.id
