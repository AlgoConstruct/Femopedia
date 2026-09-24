from unittest import mock

import pytest
from django.test import Client
from rest_framework.throttling import SimpleRateThrottle

from apps.accounts.models import Device
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
