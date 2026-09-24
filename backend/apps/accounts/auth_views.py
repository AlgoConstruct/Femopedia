from django.db import transaction
from django.utils import timezone
from drf_spectacular.utils import OpenApiResponse, extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.decorators import api_view, throttle_classes
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle

from apps.accounts.models import Account, Identifier
from apps.accounts.serializers import EmailSignupSerializer


@extend_schema(
    operation_id="signup",
    summary="Create an account and bind the calling device to it",
    description=(
        "Signing up issues no new credential: the caller already holds a "
        "device token, and this gives that device an owner by setting its "
        "account. No verification email is sent by this endpoint."
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

    with transaction.atomic():
        account = Account()
        account.set_password(serializer.validated_data["password"])
        account.save()
        Identifier.create_for(
            account, Identifier.KIND_EMAIL, serializer.validated_data["email"]
        )
        device.account = account
        device.bound_at = timezone.now()
        device.save(update_fields=["account", "bound_at"])

    return Response({"account_id": str(account.id)}, status=status.HTTP_201_CREATED)


signup.cls.throttle_scope = "auth"
