from unittest import mock

import pytest
from django.test import Client
from rest_framework.throttling import SimpleRateThrottle

from apps.accounts import account_views, auth_views, session_views
from apps.accounts import urls as accounts_urls
from apps.accounts.models import Account, Device, Identifier
from apps.accounts.throttling import IPScopedRateThrottle
from apps.accounts.tokens import generate_device_token, hash_device_token

# SimpleRateThrottle.THROTTLE_RATES is bound to real settings.REST_FRAMEWORK's
# DEFAULT_THROTTLE_RATES the first time rest_framework.throttling is imported
# -- which, because Django's URL resolver imports views lazily, can be
# triggered by whichever test in the whole suite happens to make the first
# HTTP request. override_settings(REST_FRAMEWORK=...) only takes effect if
# it happens to be active at that one moment, so it is order-dependent and
# unreliable here. Patching the class attribute directly is not.


@pytest.mark.django_db
def test_create_device_is_throttled_past_its_scoped_rate():
    """POST /api/devices/ mints a row per call, unauthenticated and
    unbounded, against the only non-rebuildable datastore -- so it carries
    its own tighter "device-create" throttle scope on top of the general
    anonymous rate. The rate is patched down to 2/hour here so the test does
    not need to make ten-plus real requests.
    """
    with mock.patch.object(
        SimpleRateThrottle,
        "THROTTLE_RATES",
        {"anon": "1000/hour", "device-create": "2/hour"},
    ):
        client = Client()
        first = client.post("/api/devices/")
        second = client.post("/api/devices/")
        third = client.post("/api/devices/")

    assert first.status_code == 201
    assert second.status_code == 201
    assert third.status_code == 429


@pytest.mark.django_db
def test_whoami_is_not_throttled_by_the_anonymous_rate_for_an_authenticated_device():
    raw = generate_device_token()
    Device.objects.create(token_hash=hash_device_token(raw))

    with mock.patch.object(SimpleRateThrottle, "THROTTLE_RATES", {"anon": "1/hour"}):
        client = Client()
        for _ in range(3):
            response = client.get("/api/whoami/", headers={"x-device-token": raw})
            assert response.status_code == 200


# --- C1: every accounts route must carry a throttle scope ------------------
#
# ScopedRateThrottle passes any view with no throttle_scope, and
# AnonRateThrottle skips authenticated requests, so before this fix
# account_summary, device_list, device_revoke, account_export and
# account_delete had no rate limit at all -- and account_delete compares a
# supplied password against the account's hash, making it an unmetered
# password oracle for anyone holding a device token. This is the convention
# test the reviewer asked for: it fails the moment a future endpoint is
# added to apps.accounts.urls without a throttle_scope, rather than relying
# on someone remembering to add one.


def test_every_accounts_route_resolves_to_a_view_carrying_a_throttle_scope():
    missing = [
        pattern.name
        for pattern in accounts_urls.urlpatterns
        if not getattr(getattr(pattern.callback, "cls", None), "throttle_scope", None)
    ]
    assert not missing, f"routes with no throttle_scope: {missing}"


@pytest.mark.django_db
def test_account_delete_is_throttled_now_that_it_carries_a_scope():
    """Was finding C1's headline case: an unmetered password oracle. Proves
    the scope actually throttles, not just that the attribute is set."""
    account = Account.objects.create()
    account.set_password("a-real-password")
    account.save()
    raw = generate_device_token()
    Device.objects.create(token_hash=hash_device_token(raw), account=account)

    with mock.patch.object(SimpleRateThrottle, "THROTTLE_RATES", {"auth": "1/hour"}):
        client = Client()
        first = client.post(
            "/api/account/delete/",
            data={"password": "wrong-password"},
            content_type="application/json",
            headers={"x-device-token": raw},
        )
        second = client.post(
            "/api/account/delete/",
            data={"password": "wrong-password"},
            content_type="application/json",
            headers={"x-device-token": raw},
        )

    assert first.status_code == 400
    assert second.status_code == 429


# --- I7: credential-checking endpoints throttle by IP, not by device -------
#
# The default ScopedRateThrottle keys its bucket on request.user.pk once
# authenticated -- here that's the Device, and POST /api/devices/ mints one
# unauthenticated and for free. Without IPScopedRateThrottle, an attacker
# could reset their attempt budget on login/recover/password-reset/
# account-delete just by minting a fresh device before every guess.

CREDENTIAL_CHECKING_VIEWS = [
    (session_views.login, "login"),
    (auth_views.recover, "recover"),
    (auth_views.password_reset, "password_reset"),
    (auth_views.password_reset_confirm, "password_reset_confirm"),
    (account_views.account_delete, "account_delete"),
]


@pytest.mark.parametrize(
    "view,name", CREDENTIAL_CHECKING_VIEWS, ids=[n for _, n in CREDENTIAL_CHECKING_VIEWS]
)
def test_credential_checking_endpoints_use_the_ip_keyed_throttle(view, name):
    assert IPScopedRateThrottle in view.cls.throttle_classes, name


@pytest.mark.django_db
def test_login_throttle_keys_on_ip_so_a_fresh_device_does_not_reset_the_bucket():
    """The behavioural proof behind the structural check above: three failed
    logins from three different, freshly minted devices -- but the same
    client, so the same REMOTE_ADDR -- still trip the throttle. Before I7,
    each new device got its own bucket and this would never trip."""
    account = Account.objects.create()
    account.set_password("a-real-password")
    account.save()
    Identifier.create_for(account, Identifier.KIND_EMAIL, "her@example.com", verified=True)

    with mock.patch.object(SimpleRateThrottle, "THROTTLE_RATES", {"auth": "2/hour"}):
        client = Client()
        statuses = []
        for _ in range(3):
            raw = generate_device_token()
            Device.objects.create(token_hash=hash_device_token(raw))
            response = client.post(
                "/api/auth/login/",
                data={"email": "her@example.com", "password": "wrong-password"},
                content_type="application/json",
                headers={"x-device-token": raw},
            )
            statuses.append(response.status_code)

    assert statuses == [401, 401, 429]
