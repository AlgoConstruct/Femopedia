from drf_spectacular.utils import OpenApiResponse, extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.core import checks

REQUIRED_SERVICES = ("postgres", "redis")
DERIVED_SERVICES = ("chroma", "neo4j")


@extend_schema(
    operation_id="health",
    summary="Liveness probe",
    description="Returns 200 whenever the process is serving requests.",
    auth=[],
    responses={
        200: inline_serializer(
            name="HealthResponse", fields={"status": serializers.CharField()}
        )
    },
)
@api_view(["GET"])
@permission_classes([AllowAny])
def health(request):
    return Response({"status": "ok"})


@extend_schema(
    operation_id="whoami",
    summary="Identify the calling device",
    description=(
        "Returns the id of the device the supplied X-Device-Token resolves to. "
        "The device id is an opaque UUID and carries no personal information."
    ),
    responses={
        200: inline_serializer(
            name="WhoamiResponse", fields={"device_id": serializers.UUIDField()}
        ),
        401: OpenApiResponse(description="Missing or unknown device token."),
    },
)
@api_view(["GET"])
def whoami(request):
    # request.user is polymorphic once Wagtail staff sessions arrive (P1.5),
    # so this reads request.auth, which DeviceTokenAuthentication populates
    # explicitly with the Device regardless of what request.user ends up being.
    return Response({"device_id": str(request.auth.id)})


@extend_schema(
    operation_id="healthDeep",
    summary="Readiness probe across every datastore",
    description=(
        "Reports reachability per datastore. Postgres and Redis are required, "
        "so either being down returns 503 with status \"down\". Chroma and "
        "Neo4j hold derived, rebuildable data, so either being down returns "
        "200 with status \"degraded\" rather than taking the API out of "
        "rotation during a rebuild."
    ),
    auth=[],
    responses={
        200: OpenApiResponse(
            description="All required services up; status is ok or degraded.",
            response=inline_serializer(
                name="HealthDeepResponse",
                fields={
                    "status": serializers.CharField(),
                    "services": inline_serializer(
                        name="HealthDeepServices",
                        fields={
                            "postgres": serializers.BooleanField(),
                            "redis": serializers.BooleanField(),
                            "chroma": serializers.BooleanField(),
                            "neo4j": serializers.BooleanField(),
                        },
                    ),
                },
            ),
        ),
        503: OpenApiResponse(description="A required datastore is unreachable."),
    },
)
@api_view(["GET"])
@permission_classes([AllowAny])
def health_deep(request):
    services = checks.run_all()
    required_up = all(services[name] for name in REQUIRED_SERVICES)
    derived_up = all(services[name] for name in DERIVED_SERVICES)

    if not required_up:
        overall = "down"
        code = status.HTTP_503_SERVICE_UNAVAILABLE
    elif not derived_up:
        # Chroma and Neo4j hold derived, rebuildable data (see plan's global
        # constraints): a rebuild in progress should read as degraded, not
        # as an outage of the whole API.
        overall = "degraded"
        code = status.HTTP_200_OK
    else:
        overall = "ok"
        code = status.HTTP_200_OK

    return Response({"status": overall, "services": services}, status=code)
