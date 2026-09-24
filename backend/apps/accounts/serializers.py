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


class UsernameSignupSerializer(serializers.Serializer):
    username = serializers.RegexField(r"^[a-zA-Z0-9_.-]{3,32}$")
    password = serializers.CharField(min_length=MIN_PASSWORD_LENGTH, write_only=True)

    def validate_username(self, value: str) -> str:
        if Identifier.lookup(Identifier.KIND_USERNAME, value) is not None:
            raise serializers.ValidationError("This username cannot be used.")
        return value


class RecoverySerializer(serializers.Serializer):
    username = serializers.CharField()
    recovery_code = serializers.CharField()
    new_password = serializers.CharField(min_length=MIN_PASSWORD_LENGTH, write_only=True)


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    token = serializers.CharField()
    new_password = serializers.CharField(min_length=MIN_PASSWORD_LENGTH, write_only=True)


class PasswordChangeSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(min_length=MIN_PASSWORD_LENGTH, write_only=True)


class AccountDeleteSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True)
