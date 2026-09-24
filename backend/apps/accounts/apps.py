from django.apps import AppConfig


class AccountsConfig(AppConfig):
    name = "apps.accounts"
    label = "accounts"

    def ready(self):
        # Importing registers DeviceTokenScheme with drf-spectacular. Without
        # this import the extension class is never loaded and the generated
        # schema silently omits the X-Device-Token security scheme.
        from apps.accounts import schema  # noqa: F401

        # Fail startup rather than silently running with a degraded
        # identifier blind index or an unusable field-encryption key (I5 of
        # the accounts-core fix wave). See apps.core.checks for why an empty
        # IDENTIFIER_PEPPER can't be caught by django-environ's own
        # required-value check.
        from apps.core.checks import validate_identifier_crypto_settings

        validate_identifier_crypto_settings()
