from django.db import transaction
from django.utils import timezone
from django.views.decorators.debug import sensitive_variables
from drf_spectacular.utils import OpenApiResponse, extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.decorators import api_view, throttle_classes
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle

from apps.accounts.models import Device, Identifier
from apps.accounts.serializers import LoginSerializer
from apps.accounts.tokens import generate_device_token, hash_device_token

INVALID_CREDENTIALS = {"detail": "Email or password is incorrect."}


@extend_schema(
    operation_id="login",
    summary="Bind the calling device to an account",
    description=(
        "Signs in by email and password, binding the calling device to the "
        "matching account. An unknown email and a wrong password answer "
        "identically, so the endpoint cannot be used to discover whether a "
        "given woman has an account here."
    ),
    request=LoginSerializer,
    responses={
        200: OpenApiResponse(
            description="The calling device is now bound to this account.",
            response=inline_serializer(
                name="LoginResponse",
                fields={"account_id": serializers.UUIDField()},
            ),
        ),
        400: OpenApiResponse(description="Invalid email or password."),
        401: OpenApiResponse(
            description="Email or password is incorrect.",
            response=inline_serializer(
                name="LoginError", fields={"detail": serializers.CharField()}
            ),
        ),
        429: OpenApiResponse(description="Rate limit exceeded."),
    },
)
@api_view(["POST"])
@throttle_classes([ScopedRateThrottle])
@sensitive_variables("password")
def login(request):
    serializer = LoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    password = serializer.validated_data["password"]

    identifier = Identifier.lookup(
        Identifier.KIND_EMAIL, serializer.validated_data["email"]
    )
    account = identifier.account if identifier else None

    # One response for "no such account" and "wrong password", so the endpoint
    # cannot be used to discover whether a given woman has an account here.
    if account is None or not account.check_password(password):
        return Response(INVALID_CREDENTIALS, status=status.HTTP_401_UNAUTHORIZED)

    device = request.auth
    device.account = account
    device.bound_at = timezone.now()
    device.save(update_fields=["account", "bound_at"])

    return Response({"account_id": str(account.id)})


@extend_schema(
    operation_id="logout",
    summary="Destroy the calling device and issue a fresh anonymous one",
    description=(
        "Deletes the calling device entirely and returns a brand-new "
        "anonymous device token. Not merely unbinding: on a shared phone, "
        "signing out must leave an application with nothing in it, rather "
        "than a sign-in screen with her history one tap behind it."
    ),
    request=None,
    responses={
        200: OpenApiResponse(
            description="The old device is gone; a fresh anonymous token is issued.",
            response=inline_serializer(
                name="LogoutResponse",
                fields={
                    "device_token": serializers.CharField(),
                    "device_id": serializers.UUIDField(),
                },
            ),
        ),
        401: OpenApiResponse(description="Missing or unknown device token."),
        429: OpenApiResponse(description="Rate limit exceeded."),
    },
)
@api_view(["POST"])
@throttle_classes([ScopedRateThrottle])
@sensitive_variables("raw_token")
def logout(request):
    """Delete this device and issue a fresh anonymous one.

    Not merely unbinding: on a shared phone, signing out must leave an
    application with nothing in it, rather than a sign-in screen with her
    history one tap behind it.
    """
    old_device = request.auth
    raw_token = generate_device_token()

    with transaction.atomic():
        new_device = Device.objects.create(
            token_hash=hash_device_token(raw_token), locale=old_device.locale
        )
        old_device.delete()

    return Response({"device_token": raw_token, "device_id": str(new_device.id)})


login.cls.throttle_scope = "auth"
logout.cls.throttle_scope = "auth"
