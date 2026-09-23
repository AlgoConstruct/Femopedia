from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.accounts.models import Device
from apps.accounts.tokens import generate_device_token, hash_device_token


@api_view(["POST"])
@permission_classes([AllowAny])
def create_device(request):
    """Issue an anonymous device token. The raw token is returned once and never stored."""
    raw_token = generate_device_token()
    device = Device.objects.create(
        token_hash=hash_device_token(raw_token),
        locale=request.data.get("locale", "ne") if isinstance(request.data, dict) else "ne",
    )
    return Response(
        {"device_id": str(device.id), "device_token": raw_token},
        status=status.HTTP_201_CREATED,
    )
