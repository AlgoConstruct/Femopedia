from django.core.signing import BadSignature
from django.db import IntegrityError, transaction
from django.utils import timezone
from django.views.decorators.debug import sensitive_variables
from drf_spectacular.utils import OpenApiResponse, extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle

from apps.accounts import verification
from apps.accounts.models import Account, Device, Identifier
from apps.accounts.serializers import EmailSignupSerializer, LoginSerializer
from apps.accounts.tokens import generate_device_token, hash_device_token

# Matches the shape DRF's default exception handler produces when
# EmailSignupSerializer.validate_email raises its ValidationError. Used
# again below for the race where two concurrent signups pass validation for
# the same address and the loser hits the database's unique constraint
# instead -- that caller must be indistinguishable from the ordinary
# duplicate-email case, both in status code and in body.
DUPLICATE_EMAIL_ERROR = {"email": ["This email cannot be used."]}


@extend_schema(
    operation_id="signup",
    summary="Create an account and bind the calling device to it",
    description=(
        "Signing up issues no new credential: the caller already holds a "
        "device token, and this gives that device an owner by setting its "
        "account. A verification email is sent to the address afterward."
    ),
    request=EmailSignupSerializer,
    responses={
        201: OpenApiResponse(
            description="Account created and the calling device bound to it.",
            response=inline_serializer(
                name="SignupResponse",
                fields={"account_id": serializers.UUIDField()},
            ),
        ),
        400: OpenApiResponse(description="Invalid email or password."),
        401: OpenApiResponse(description="Missing or unknown device token."),
        409: OpenApiResponse(description="The calling device is already signed in."),
        429: OpenApiResponse(description="Rate limit exceeded."),
    },
)
@api_view(["POST"])
@throttle_classes([ScopedRateThrottle])
@sensitive_variables("password")
def signup(request):
    """Create an account and bind the calling device to it.

    The caller is already an anonymous device; signing up does not issue a new
    credential, it gives the existing one an owner.
    """
    device = request.auth
    if device.account_id is not None:
        return Response(
            {"detail": "This device is already signed in."},
            status=status.HTTP_409_CONFLICT,
        )

    serializer = EmailSignupSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    email = serializer.validated_data["email"]
    password = serializer.validated_data["password"]

    try:
        with transaction.atomic():
            account = Account()
            account.set_password(password)
            account.save()
            identifier = Identifier.create_for(account, Identifier.KIND_EMAIL, email)
            device.account = account
            device.bound_at = timezone.now()
            device.save(update_fields=["account", "bound_at"])
    except IntegrityError:
        # The serializer's own duplicate-email check already handles the
        # common case; this is the loser of a race between two concurrent
        # signups for the same address, caught by the database's unique
        # constraint on (kind, value_hash) instead. Answer the same way the
        # serializer would have, rather than letting an IntegrityError
        # surface as a 500 or the vague-error wording get bypassed.
        return Response(DUPLICATE_EMAIL_ERROR, status=status.HTTP_400_BAD_REQUEST)

    # Outside the transaction: a mail failure must not roll back an account
    # that was successfully created. She can re-request verification, but
    # she cannot re-create an account that vanished.
    verification.send_verification_email(identifier)

    return Response({"account_id": str(account.id)}, status=status.HTTP_201_CREATED)


signup.cls.throttle_scope = "auth"


@extend_schema(
    operation_id="verifyEmail",
    summary="Confirm an email address",
    description=(
        "Confirms an email address from the link sent by signup. Deliberately "
        "AllowAny: she may open the link on a device that has never used the "
        "application, and requiring a device token there would strand her."
    ),
    auth=[],
    request=inline_serializer(
        name="VerifyEmailRequest",
        fields={"token": serializers.CharField()},
    ),
    responses={
        200: OpenApiResponse(
            description="The identifier is now verified.",
            response=inline_serializer(
                name="VerifyEmailResponse", fields={"status": serializers.CharField()}
            ),
        ),
        400: OpenApiResponse(
            description="The token is invalid or has expired.",
            response=inline_serializer(
                name="VerifyEmailError", fields={"detail": serializers.CharField()}
            ),
        ),
        429: OpenApiResponse(description="Rate limit exceeded."),
    },
)
@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([ScopedRateThrottle])
def verify_email(request):
    """Confirm an email address.

    Deliberately AllowAny: she may open the link on a device that has never
    used the application, and requiring a device token there would strand her.
    """
    token = request.data.get("token", "") if isinstance(request.data, dict) else ""
    try:
        identifier_id = verification.read_token(token)
    except BadSignature:
        return Response(
            {"detail": "This link is invalid or has expired."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    updated = Identifier.objects.filter(
        id=identifier_id, verified_at__isnull=True
    ).update(verified_at=timezone.now())

    if not updated and not Identifier.objects.filter(id=identifier_id).exists():
        return Response(
            {"detail": "This link is invalid or has expired."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    return Response({"status": "verified"})


verify_email.cls.throttle_scope = "auth"

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

    identifier = Identifier.lookup(
        Identifier.KIND_EMAIL, serializer.validated_data["email"]
    )
    account = identifier.account if identifier else None

    # One response for "no such account" and "wrong password", so the endpoint
    # cannot be used to discover whether a given woman has an account here.
    if account is None or not account.check_password(
        serializer.validated_data["password"]
    ):
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
