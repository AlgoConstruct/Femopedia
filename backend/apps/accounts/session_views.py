from django.contrib.auth.hashers import check_password as django_check_password
from django.contrib.auth.hashers import make_password
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
from apps.accounts.throttling import IPScopedRateThrottle
from apps.accounts.tokens import generate_device_token, hash_device_token

INVALID_CREDENTIALS = {"detail": "Email or password is incorrect."}

# A password hash for a password nobody will ever type, used only to burn
# the same PBKDF2 time a real check_password() call would spend (C3 of the
# accounts-core fix wave). Without this, an unknown email returns in ~5ms
# while a known email with a wrong password takes ~250ms+ -- the cost of
# actually running the hasher -- and that gap is a reliable way to learn
# whether a given address has an account here. Django's own
# ModelBackend.authenticate() does the equivalent thing, for the same reason.
_DUMMY_PASSWORD_HASH = make_password("dummy-password-nobody-will-ever-type")


@extend_schema(
    operation_id="login",
    summary="Bind the calling device to an account",
    description=(
        "Signs in by email and password, binding the calling device to the "
        "matching account. An unknown email and a wrong password answer "
        "identically, so the endpoint cannot be used to discover whether a "
        "given woman has an account here.\n\n"
        "If the calling device is already signed in -- to this account or "
        "to a different one -- this is a logout-then-login, exactly like "
        "POST /api/auth/logout/ followed by a fresh sign-in: the old device "
        "row is deleted and a brand-new one is created, bound to the "
        "account just authenticated, and its token is returned as "
        "device_token/device_id alongside account_id. Nothing is silently "
        "transferred between accounts. This matters because two women "
        "sharing a handset is a central scenario: logging in as one must "
        "never quietly attach her history to whoever was signed in before "
        "her."
    ),
    request=LoginSerializer,
    responses={
        200: OpenApiResponse(
            description=(
                "The calling device is now bound to this account. "
                "device_token and device_id are present only when the "
                "calling device was already signed in and had to be "
                "replaced (see the rebind note above)."
            ),
            response=inline_serializer(
                name="LoginResponse",
                fields={
                    "account_id": serializers.UUIDField(),
                    "device_token": serializers.CharField(required=False),
                    "device_id": serializers.UUIDField(required=False),
                },
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
@throttle_classes([IPScopedRateThrottle])
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
    if account is None:
        # No such account: run the password hasher anyway, against a fixed
        # dummy hash, and discard the result. See _DUMMY_PASSWORD_HASH above
        # -- skipping this is what turns response time into an oracle.
        django_check_password(password, _DUMMY_PASSWORD_HASH)
        return Response(INVALID_CREDENTIALS, status=status.HTTP_401_UNAUTHORIZED)
    if not account.check_password(password):
        return Response(INVALID_CREDENTIALS, status=status.HTTP_401_UNAUTHORIZED)

    device = request.auth
    if device.account_id is not None:
        # The calling device is already signed in -- possibly to this very
        # account, possibly to someone else's (I8 of the accounts-core fix
        # wave). Either way, rebind by logout-then-login rather than
        # mutating the existing row in place: a shared handset must never
        # let logging in as one woman silently carry over to a device
        # another woman was using, and a device row that changes owner
        # in place is exactly that risk.
        raw_token = generate_device_token()
        with transaction.atomic():
            new_device = Device.objects.create(
                token_hash=hash_device_token(raw_token),
                locale=device.locale,
                account=account,
                bound_at=timezone.now(),
            )
            device.delete()
        return Response(
            {
                "account_id": str(account.id),
                "device_token": raw_token,
                "device_id": str(new_device.id),
            }
        )

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
