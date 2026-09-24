from django.utils import timezone
from django.views.decorators.debug import sensitive_variables
from rest_framework import authentication, exceptions

from apps.accounts.models import Device
from apps.accounts.tokens import hash_device_token

HEADER = "HTTP_X_DEVICE_TOKEN"


class DeviceTokenAuthentication(authentication.BaseAuthentication):
    """Resolve the X-Device-Token header to a Device.

    The raw token never leaves the client after issuance; only its hash is
    compared here, so a database leak does not yield usable credentials.
    """

    @sensitive_variables("raw_token")
    def authenticate(self, request):
        raw_token = request.META.get(HEADER)
        if not raw_token:
            return None

        try:
            device = Device.objects.get(token_hash=hash_device_token(raw_token))
        except Device.DoesNotExist:
            raise exceptions.AuthenticationFailed("Unknown device token.")

        # An anonymous device has no owner to show a label to, so writing one
        # is a plaintext handset fingerprint sitting on a row that used to
        # hold only a hash and a locale -- the branch's one anonymity
        # regression (finding I4 of the accounts-core fix wave). Only a
        # device with an account records the User-Agent it authenticates
        # with, so she can tell devices apart on her own session list.
        update_fields = {"last_seen": timezone.now()}
        if device.account_id is not None:
            update_fields["label"] = (request.META.get("HTTP_USER_AGENT") or "")[:120]
        Device.objects.filter(pk=device.pk).update(**update_fields)
        # request.auth carries the device explicitly, so callers do not need
        # to guess which authenticator populated request.user (see
        # apps.core.views.whoami and finding 10 of the P0 fix wave).
        return (device, device)

    def authenticate_header(self, request):
        return "X-Device-Token"
