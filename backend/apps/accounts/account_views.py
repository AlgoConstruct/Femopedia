from drf_spectacular.utils import OpenApiResponse, extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from apps.accounts.models import Device

NOT_SIGNED_IN = OpenApiResponse(
    description="This device is not signed in.",
    response=inline_serializer(
        name="AccountForbidden", fields={"detail": serializers.CharField()}
    ),
)


def _require_account(request):
    """Return the caller's account, or None when the device is anonymous."""
    return request.auth.account


@extend_schema(
    operation_id="accountSummary",
    summary="Summarize the calling account",
    description=(
        "Returns the account id, creation time, and the kind and "
        "verification status of each identifier on the account. Identifier "
        "values are encrypted at rest and are never returned here."
    ),
    responses={
        200: inline_serializer(
            name="AccountSummaryResponse",
            fields={
                "account_id": serializers.UUIDField(),
                "created_at": serializers.DateTimeField(),
                "identifiers": inline_serializer(
                    name="AccountIdentifierSummary",
                    fields={
                        "kind": serializers.CharField(),
                        "verified": serializers.BooleanField(),
                    },
                    many=True,
                ),
            },
        ),
        403: NOT_SIGNED_IN,
    },
)
@api_view(["GET"])
def account_summary(request):
    account = _require_account(request)
    if account is None:
        return Response(
            {"detail": "This device is not signed in."},
            status=status.HTTP_403_FORBIDDEN,
        )

    # Kinds and verification status only. The values themselves are encrypted
    # at rest and there is no reason for a summary screen to decrypt them.
    identifiers = [
        {"kind": i.kind, "verified": i.is_verified}
        for i in account.identifiers.order_by("created_at")
    ]
    return Response(
        {
            "account_id": str(account.id),
            "created_at": account.created_at.isoformat(),
            "identifiers": identifiers,
        }
    )


@extend_schema(
    operation_id="accountDevices",
    summary="List every device bound to the calling account",
    description=(
        "Returns every device signed in to this account, so she can "
        "recognize a phone she no longer has, or one someone else now uses. "
        "The device token hash is never included."
    ),
    responses={
        200: inline_serializer(
            name="AccountDeviceListResponse",
            fields={
                "devices": inline_serializer(
                    name="AccountDevice",
                    fields={
                        "id": serializers.UUIDField(),
                        "label": serializers.CharField(),
                        "last_seen": serializers.DateTimeField(),
                        "bound_at": serializers.DateTimeField(allow_null=True),
                        "is_current": serializers.BooleanField(),
                    },
                    many=True,
                )
            },
        ),
        403: NOT_SIGNED_IN,
    },
)
@api_view(["GET"])
def device_list(request):
    account = _require_account(request)
    if account is None:
        return Response(
            {"detail": "This device is not signed in."},
            status=status.HTTP_403_FORBIDDEN,
        )

    current_id = request.auth.id
    devices = [
        {
            "id": str(device.id),
            "label": device.label,
            "last_seen": device.last_seen.isoformat(),
            "bound_at": device.bound_at.isoformat() if device.bound_at else None,
            "is_current": device.id == current_id,
        }
        for device in account.devices.order_by("-last_seen")
    ]
    return Response({"devices": devices})


@extend_schema(
    operation_id="accountDeviceRevoke",
    summary="Revoke a device bound to the calling account",
    description=(
        "Deletes a device belonging to the calling account, dropping a "
        "phone she no longer has or one someone else now uses. A device id "
        "that belongs to another account is indistinguishable from one that "
        "does not exist: both answer 404, never 403, so this cannot be used "
        "to confirm who owns a given device."
    ),
    responses={
        204: OpenApiResponse(description="The device is gone."),
        403: NOT_SIGNED_IN,
        404: OpenApiResponse(
            description="No such device on this account.",
            response=inline_serializer(
                name="AccountDeviceNotFound", fields={"detail": serializers.CharField()}
            ),
        ),
    },
)
@api_view(["DELETE"])
def device_revoke(request, device_id):
    account = _require_account(request)
    if account is None:
        return Response(
            {"detail": "This device is not signed in."},
            status=status.HTTP_403_FORBIDDEN,
        )

    # Scoped to her own devices: a device belonging to someone else must be
    # indistinguishable from one that does not exist.
    deleted, _ = Device.objects.filter(id=device_id, account=account).delete()
    if not deleted:
        return Response(
            {"detail": "No such device."}, status=status.HTTP_404_NOT_FOUND
        )
    return Response(status=status.HTTP_204_NO_CONTENT)
