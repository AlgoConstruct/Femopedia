from django.apps import AppConfig


class AccountsConfig(AppConfig):
    name = "apps.accounts"
    label = "accounts"

    def ready(self):
        # Importing registers DeviceTokenScheme with drf-spectacular. Without
        # this import the extension class is never loaded and the generated
        # schema silently omits the X-Device-Token security scheme.
        from apps.accounts import schema  # noqa: F401
