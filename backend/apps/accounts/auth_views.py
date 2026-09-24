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
from apps.accounts.models import Account, Identifier
from apps.accounts.serializers import EmailSignupSerializer

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
