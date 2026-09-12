"""
DRF serializers for authentication and profile endpoints.

Mirrors the validation rules in ``account_manager/forms.py`` (RegisterForm,
LoginForm) so the API and the server-rendered app accept the same credentials.
"""
import re

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

from rest_framework import serializers
from rest_framework_simplejwt.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()

# Matches the complexity checks in RegisterForm.clean_password.
_PASSWORD_SPECIAL = re.compile(r"[!@#$%^&*(),.?\":{}|<>]")


class RegisterSerializer(serializers.ModelSerializer):
    """Create a user with validated username / email / password.

    Privilege fields (is_staff, is_superuser, groups, permissions) are never
    accepted: they are absent from ``Meta.fields``, so extra input is ignored
    and ``create`` only sets safe attributes.
    """

    password = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
    )
    confirm_password = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
    )

    class Meta:
        model = User
        fields = (
            "first_name",
            "username",
            "email",
            "password",
            "confirm_password",
        )

    def validate_password(self, value):
        # Django's built-in validators (minimum length, common/numeric
        # passwords, username similarity).
        validate_password(value)
        if not re.search(r"[A-Z]", value):
            raise serializers.ValidationError(
                "Password must contain at least one uppercase letter."
            )
        if not re.search(r"[a-z]", value):
            raise serializers.ValidationError(
                "Password must contain at least one lowercase letter."
            )
        if not re.search(r"\d", value):
            raise serializers.ValidationError(
                "Password must contain at least one number."
            )
        if not _PASSWORD_SPECIAL.search(value):
            raise serializers.ValidationError(
                "Password must contain at least one special character."
            )
        return value

    def validate_email(self, value):
        value = (value or "").strip().lower()
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError(
                "An account with this email already exists."
            )
        return value

    def validate(self, attrs):
        password = attrs.get("password")
        confirm = attrs.get("confirm_password")
        if password != confirm:
            raise serializers.ValidationError("Passwords do not match.")
        return attrs

    def create(self, validated_data):
        validated_data.pop("confirm_password", None)
        # create_user applies set_password and never interprets privilege
        # fields (none are passed through).
        return User.objects.create_user(**validated_data)


class UserSerializer(serializers.ModelSerializer):
    """Safe public representation of a user. Never exposes password/hash."""

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "date_joined",
        )
        read_only_fields = fields


class ProfileSerializer(serializers.ModelSerializer):
    """Read/write access to safe profile fields only.

    Privilege fields (is_staff, is_superuser, groups, permissions) are absent
    from ``Meta.fields``, so they can never be modified through the API.
    """

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "date_joined",
        )
        read_only_fields = ("id", "username", "date_joined")

    def validate_email(self, value):
        value = (value or "").strip().lower()
        user = self.instance
        if User.objects.filter(email__iexact=value).exclude(pk=user.pk).exists():
            raise serializers.ValidationError(
                "An account with this email already exists."
            )
        return value


class EmailOrUsernameTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Token login that accepts a username *or* an email, like LoginForm."""

    def validate(self, attrs):
        identifier = attrs.get(self.username_field, "") or ""
        if "@" in identifier:
            try:
                user = User.objects.get(email__iexact=identifier)
            except User.DoesNotExist:
                raise AuthenticationFailed(
                    "Invalid username/email or password.",
                    code="no_active_account",
                )
            # Re-point the credential lookup at the real username.
            attrs[self.username_field] = user.username
        return super().validate(attrs)