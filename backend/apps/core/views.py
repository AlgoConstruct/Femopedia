from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.core import checks

REQUIRED_SERVICES = ("postgres", "redis")
DERIVED_SERVICES = ("chroma", "neo4j")


@api_view(["GET"])
@permission_classes([AllowAny])
def health(request):
    return Response({"status": "ok"})


@api_view(["GET"])
def whoami(request):
    # request.user is polymorphic once Wagtail staff sessions arrive (P1.5),
    # so this reads request.auth, which DeviceTokenAuthentication populates
    # explicitly with the Device regardless of what request.user ends up being.
    return Response({"device_id": str(request.auth.id)})


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
