from drf_spectacular.extensions import OpenApiAuthenticationExtension


class DeviceTokenScheme(OpenApiAuthenticationExtension):
    """Teach the schema generator about DeviceTokenAuthentication.

    Without this, spectacular cannot describe a custom authentication class and
    emits an endpoint with no security requirement, which would document the
    API as open when it is not.
    """

    target_class = "apps.accounts.authentication.DeviceTokenAuthentication"
    name = "DeviceToken"

    def get_security_definition(self, auto_schema):
        return {
            "type": "apiKey",
            "in": "header",
            "name": "X-Device-Token",
            "description": (
                "The token returned once by POST /api/devices/. The server "
                "stores only its SHA-256 hash, so it cannot be recovered if "
                "the client loses it."
            ),
        }
