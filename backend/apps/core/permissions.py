import secrets

from django.conf import settings
from rest_framework.permissions import BasePermission


class SchemaAccess(BasePermission):
    """Allow access to the OpenAPI schema and its UI.

    The schema enumerates every endpoint, which is exactly the map an attacker
    would otherwise have to build by hand, so it is not public. Access is
    granted under DEBUG for local work, or to a caller presenting the shared
    DOCS_TOKEN. An unset DOCS_TOKEN denies the token path outright rather than
    degrading to an empty-string comparison that anything would satisfy.
    """

    message = "Schema access requires DEBUG or a valid X-Docs-Token header."

    def has_permission(self, request, view):
        if settings.DEBUG:
            return True

        expected = settings.DOCS_TOKEN
        if not expected:
            return False

        provided = request.headers.get("X-Docs-Token", "")
        return secrets.compare_digest(provided, expected)
