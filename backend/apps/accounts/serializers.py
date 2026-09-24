from rest_framework import serializers

from apps.accounts.models import Identifier

MIN_PASSWORD_LENGTH = 10


class EmailSignupSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(min_length=MIN_PASSWORD_LENGTH, write_only=True)

    def validate_email(self, value: str) -> str:
        if Identifier.lookup(Identifier.KIND_EMAIL, value) is not None:
            # Deliberately the same shape of error as any other validation
            # failure. This endpoint requires a device token, so it is not an
            # open oracle, but there is no reason to confirm an address more
            # loudly than necessary.
            raise serializers.ValidationError("This email cannot be used.")
        return value


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
