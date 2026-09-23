from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.core import checks


@api_view(["GET"])
@permission_classes([AllowAny])
def health(request):
    return Response({"status": "ok"})


@api_view(["GET"])
def whoami(request):
    return Response({"device_id": str(request.user.id)})


@api_view(["GET"])
@permission_classes([AllowAny])
def health_deep(request):
    services = checks.run_all()
    code = status.HTTP_200_OK if all(services.values()) else status.HTTP_503_SERVICE_UNAVAILABLE
    return Response({"services": services}, status=code)
