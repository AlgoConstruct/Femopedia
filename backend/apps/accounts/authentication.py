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

        Device.objects.filter(pk=device.pk).update(last_seen=timezone.now())
        return (device, None)

    def authenticate_header(self, request):
        return "X-Device-Token"
