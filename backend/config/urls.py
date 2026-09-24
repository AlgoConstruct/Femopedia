from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from apps.core.permissions import SchemaAccess

# The schema routes are always registered, and access is decided per request by
# SchemaAccess. Gating on DEBUG at import time instead would make the routes
# untestable without reloading the URLConf, and would leave no way to open the
# docs on a deployed environment when that is genuinely wanted.
#
# authentication_classes is emptied deliberately. With DeviceTokenAuthentication
# in play, DRF answers a denial with 401 and a WWW-Authenticate header naming
# X-Device-Token, which invites the caller to retry with a device token that
# would never grant schema access. With no authenticator, denial is a plain 403:
# not "authenticate yourself", but "this is not yours to read".
schema_view = SpectacularAPIView.as_view(
    permission_classes=[SchemaAccess], authentication_classes=[], throttle_classes=[]
)

urlpatterns = [
    path("api/", include("apps.core.urls")),
    path("api/", include("apps.accounts.urls")),
    path("api/schema/", schema_view, name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(
            url_name="schema",
            permission_classes=[SchemaAccess],
            authentication_classes=[],
            throttle_classes=[],
        ),
        name="swagger-ui",
    ),
    path(
        "api/redoc/",
        SpectacularRedocView.as_view(
            url_name="schema",
            permission_classes=[SchemaAccess],
            authentication_classes=[],
            throttle_classes=[],
        ),
        name="redoc",
    ),
]
