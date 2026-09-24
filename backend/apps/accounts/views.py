from django.views.decorators.debug import sensitive_variables
from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.accounts.models import SUPPORTED_LOCALES, Device
from apps.accounts.tokens import generate_device_token, hash_device_token


@extend_schema(
    operation_id="createDevice",
    summary="Issue an anonymous device token",
    description=(
        "Creates an anonymous device and returns its token. The token is shown "
        "exactly once; only its SHA-256 hash is stored, so a lost token cannot "
        "be recovered and a database leak yields no usable credential. No "
        "personal identifier is required or accepted."
    ),
    auth=[],
    request=inline_serializer(
        name="CreateDeviceRequest",
        fields={
            "locale": serializers.ChoiceField(
                choices=SUPPORTED_LOCALES, required=False, default="ne"
            )
        },
    ),
    responses={
        201: OpenApiResponse(
            description="Device created.",
            response=inline_serializer(
                name="CreateDeviceResponse",
                fields={
                    "device_id": serializers.UUIDField(),
                    "device_token": serializers.CharField(),
                },
            ),
            examples=[
                OpenApiExample(
                    "Created",
                    value={
                        "device_id": "3f2a1c64-5b7e-4e0a-9d2c-8e6b1f0a7c41",
                        "device_token": "kR3v9Qw1xTzB7nS5mH2pL8dY4cJ6gA0eUfV-oXbNiZk",
                    },
                )
            ],
        ),
        400: OpenApiResponse(
            description="Unsupported or malformed locale.",
            response=inline_serializer(
                name="ErrorDetail", fields={"detail": serializers.CharField()}
            ),
        ),
        429: OpenApiResponse(description="Rate limit exceeded."),
    },
)
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
