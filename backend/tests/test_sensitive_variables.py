"""Confirm raw device tokens are cleansed from traceback frame locals.

Django's SafeExceptionReporterFilter only scrubs local variables named by
@sensitive_variables when settings.DEBUG is False (see
SafeExceptionReporterFilter.is_active) -- the assumption being that a DEBUG
site is unsafe anyway. That is also the condition under which an error
reporter such as Sentry would actually be wired up, so these tests exercise
that path directly rather than asserting anything about request.META (which
Django already cleanses on its own via a separate, unrelated mechanism).
"""

import sys
from unittest import mock

import pytest
from django.test import RequestFactory, override_settings
from django.views.debug import get_exception_reporter_filter
from rest_framework.exceptions import AuthenticationFailed

from apps.accounts import views as accounts_views
from apps.accounts.authentication import DeviceTokenAuthentication


def _cleansed_locals_for_frame(frame_name, tb):
    """Walk a traceback to the named frame and return its cleansed locals."""
    current = tb
    target_frame = None
    while current is not None:
        if current.tb_frame.f_code.co_name == frame_name:
            target_frame = current.tb_frame
        current = current.tb_next
    assert target_frame is not None, f"no frame named {frame_name!r} in traceback"
    report_filter = get_exception_reporter_filter(None)
    return dict(report_filter.get_traceback_frame_variables(None, target_frame))


@pytest.mark.django_db
def test_authenticate_cleanses_raw_token_from_its_frame_locals():
    request = RequestFactory().get("/api/whoami/", HTTP_X_DEVICE_TOKEN="totally-bogus-token")

    with override_settings(DEBUG=False):
        try:
            DeviceTokenAuthentication().authenticate(request)
        except AuthenticationFailed:
            cleansed = _cleansed_locals_for_frame("authenticate", sys.exc_info()[2])
        else:
            raise AssertionError("authenticate() was expected to raise for an unknown token")

    assert cleansed["raw_token"] == "********************"


def test_create_device_cleanses_raw_token_from_its_frame_locals():
    request = RequestFactory().post("/api/devices/", data={}, content_type="application/json")

    with (
        mock.patch(
            "apps.accounts.views.Device.objects.create", side_effect=RuntimeError("db exploded")
        ),
        override_settings(DEBUG=False),
    ):
        try:
            accounts_views.create_device(request)
        except RuntimeError:
            cleansed = _cleansed_locals_for_frame("create_device", sys.exc_info()[2])
        else:
            raise AssertionError("create_device() was expected to raise when Device.create fails")

    assert cleansed["raw_token"] == "********************"
