import secrets

from django.core.signing import BadSignature
from django.db import IntegrityError, transaction
from django.utils import timezone
from django.views.decorators.debug import sensitive_variables
from drf_spectacular.utils import (
    OpenApiResponse,
    PolymorphicProxySerializer,
    extend_schema,
    inline_serializer,
)
from rest_framework import serializers, status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle

from apps.accounts import verification
from apps.accounts.models import Account, Device, Identifier
from apps.accounts.serializers import (
    EmailSignupSerializer,
    LoginSerializer,
    RecoverySerializer,
    UsernameSignupSerializer,
)
from apps.accounts.tokens import (
    generate_device_token,
    generate_recovery_code,
    hash_device_token,
    hash_recovery_code,
)

# Matches the shape DRF's default exception handler produces when
# EmailSignupSerializer.validate_email / UsernameSignupSerializer.validate_username
# raises its ValidationError. Used again below for the race where two
# concurrent signups pass validation for the same address or username and the
# loser hits the database's unique constraint on (kind, value_hash) instead
# -- that caller must be indistinguishable from the ordinary
# duplicate-email/duplicate-username case, both in status code and in body.
DUPLICATE_EMAIL_ERROR = {"email": ["This email cannot be used."]}
DUPLICATE_USERNAME_ERROR = {"username": ["This username cannot be used."]}


@extend_schema(
    operation_id="signup",
    summary="Create an account and bind the calling device to it",
    description=(
        "Signing up issues no new credential: the caller already holds a "
        "device token, and this gives that device an owner by setting its "
        "account. An email signup sends a verification email afterward. A "
        "username signup has no email to send to, so instead it returns a "
        "recovery code -- shown exactly once, here, and never again."
    ),
    request=PolymorphicProxySerializer(
        component_name="Signup",
        serializers=[EmailSignupSerializer, UsernameSignupSerializer],
        resource_type_field_name=None,
    ),
    responses={
        201: OpenApiResponse(
            description=(
                "Account created and the calling device bound to it. "
                "recovery_code is present only for a username signup."
            ),
            response=inline_serializer(
                name="SignupResponse",
                fields={
                    "account_id": serializers.UUIDField(),
                    "recovery_code": serializers.CharField(required=False),
                },
            ),
        ),
        400: OpenApiResponse(
            description="Invalid payload, or neither an email nor a username."
        ),
        401: OpenApiResponse(description="Missing or unknown device token."),
        409: OpenApiResponse(description="The calling device is already signed in."),
        429: OpenApiResponse(description="Rate limit exceeded."),
    },
)
@api_view(["POST"])
@throttle_classes([ScopedRateThrottle])
@sensitive_variables("password", "recovery_code")
def signup(request):
    """Create an account and bind the calling device to it.

    The caller is already an anonymous device; signing up does not issue a new
    credential, it gives the existing one an owner. An email payload creates
    an email-identified account; a username payload creates a contact-less
    one with a recovery code instead -- there is no email to fall back on.
    """
    device = request.auth
    if device.account_id is not None:
        return Response(
            {"detail": "This device is already signed in."},
            status=status.HTTP_409_CONFLICT,
        )

    payload = request.data if isinstance(request.data, dict) else {}
    if "email" in payload:
        serializer = EmailSignupSerializer(data=payload)
    elif "username" in payload:
        serializer = UsernameSignupSerializer(data=payload)
    else:
        return Response(
            {"detail": "Provide either an email or a username."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    serializer.is_valid(raise_exception=True)

    password = serializer.validated_data["password"]
    recovery_code = None

    try:
        with transaction.atomic():
            account = Account()
            account.set_password(password)
            if isinstance(serializer, UsernameSignupSerializer):
                recovery_code = generate_recovery_code()
                account.recovery_code_hash = hash_recovery_code(recovery_code)
            account.save()

            if isinstance(serializer, EmailSignupSerializer):
                identifier = Identifier.create_for(
                    account, Identifier.KIND_EMAIL, serializer.validated_data["email"]
                )
            else:
                identifier = None
                Identifier.create_for(
                    account,
                    Identifier.KIND_USERNAME,
                    serializer.validated_data["username"],
                )

            device.account = account
            device.bound_at = timezone.now()
            device.save(update_fields=["account", "bound_at"])
    except IntegrityError:
        # The serializer's own duplicate check already handles the common
        # case; this is the loser of a race between two concurrent signups
        # for the same address or username, caught by the database's unique
        # constraint on (kind, value_hash) instead. Answer the same way the
        # matching serializer would have -- an email collision must not come
        # back naming "username", and vice versa -- rather than letting an
        # IntegrityError surface as a 500 or the vague-error wording get
        # bypassed.
        error = (
            DUPLICATE_EMAIL_ERROR
            if isinstance(serializer, EmailSignupSerializer)
            else DUPLICATE_USERNAME_ERROR
        )
        return Response(error, status=status.HTTP_400_BAD_REQUEST)

    # Outside the transaction: a mail failure must not roll back an account
    # that was successfully created. She can re-request verification, but
    # she cannot re-create an account that vanished.
    if identifier is not None:
        verification.send_verification_email(identifier)

    body = {"account_id": str(account.id)}
    if recovery_code is not None:
        body["recovery_code"] = recovery_code
    return Response(body, status=status.HTTP_201_CREATED)


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

RECOVERY_FAILURE = {"detail": "That username and recovery code do not match."}


@extend_schema(
    operation_id="recover",
    summary="Reset a password with a recovery code and issue a replacement",
    description=(
        "Sets a new password using a recovery code, and issues a replacement "
        "code -- the old one is spent, single-use. Deliberately AllowAny: a "
        "woman recovering an account may be on a new device with no token "
        "yet, and requiring one would strand exactly the person this "
        "endpoint exists for. Every failure -- unknown username, wrong code, "
        "no code set -- answers identically, so the endpoint cannot be used "
        "to discover which usernames exist."
    ),
    auth=[],
    request=RecoverySerializer,
    responses={
        200: OpenApiResponse(
            description="The password is reset; this is the replacement code.",
            response=inline_serializer(
                name="RecoverResponse",
                fields={"recovery_code": serializers.CharField()},
            ),
        ),
        400: OpenApiResponse(
            description="Invalid payload, or the username and code do not match.",
            response=inline_serializer(
                name="RecoverError", fields={"detail": serializers.CharField()}
            ),
        ),
        429: OpenApiResponse(description="Rate limit exceeded."),
    },
)
@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([ScopedRateThrottle])
@sensitive_variables("recovery_code", "new_password")
def recover(request):
    """Set a new password using a recovery code, and issue a replacement code.

    AllowAny because a woman recovering an account may be on a new device
    that has no token yet. Every failure answers identically, so the
    endpoint cannot be used to discover which usernames exist.
    """
    serializer = RecoverySerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    failure = Response(RECOVERY_FAILURE, status=status.HTTP_400_BAD_REQUEST)

    recovery_code = serializer.validated_data["recovery_code"]
    new_password = serializer.validated_data["new_password"]

    identifier = Identifier.lookup(
        Identifier.KIND_USERNAME, serializer.validated_data["username"]
    )
    if identifier is None:
        return failure

    account = identifier.account
    supplied = hash_recovery_code(recovery_code)
    # The `not account.recovery_code_hash` short-circuit is currently
    # inconsequential -- every account reachable via a username identifier
    # was given a recovery code at signup, so this is never empty here in
    # practice. It would need revisiting if a code could ever be revoked
    # without a replacement being issued.
    if not account.recovery_code_hash or not secrets.compare_digest(
        supplied, account.recovery_code_hash
    ):
        return failure

    replacement = generate_recovery_code()
    account.set_password(new_password)
    account.recovery_code_hash = hash_recovery_code(replacement)
    account.recovery_code_used_at = timezone.now()
    account.save(
        update_fields=["password", "recovery_code_hash", "recovery_code_used_at"]
    )

    return Response({"recovery_code": replacement})


recover.cls.throttle_scope = "auth"

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
