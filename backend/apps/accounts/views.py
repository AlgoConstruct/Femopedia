from django.views.decorators.debug import sensitive_variables
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.accounts.models import SUPPORTED_LOCALES, Device
from apps.accounts.tokens import generate_device_token, hash_device_token


@api_view(["POST"])
@permission_classes([AllowAny])
@sensitive_variables("raw_token")
def create_device(request):
    """Issue an anonymous device token. The raw token is returned once and never stored."""
    locale = request.data.get("locale", "ne") if isinstance(request.data, dict) else "ne"
    if not isinstance(locale, str) or locale not in SUPPORTED_LOCALES:
        return Response(
            {"detail": "locale must be one of: " + ", ".join(SUPPORTED_LOCALES)},
            status=status.HTTP_400_BAD_REQUEST,
        )

    raw_token = generate_device_token()
    device = Device.objects.create(
        token_hash=hash_device_token(raw_token),
        locale=locale,
    )
    return Response(
        {"device_id": str(device.id), "device_token": raw_token},
        status=status.HTTP_201_CREATED,
    )


# Ties this view to the "device-create" throttle rate in REST_FRAMEWORK's
# DEFAULT_THROTTLE_RATES; ScopedRateThrottle only throttles views that carry
# this attribute, so every other view is unaffected by it.
create_device.cls.throttle_scope = "device-create"
