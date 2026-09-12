"""
DRF API views for authentication and profile.
"""
from django.contrib.auth import get_user_model

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView

from .serializers import (
    EmailOrUsernameTokenObtainPairSerializer,
    ProfileSerializer,
    RegisterSerializer,
    UserSerializer,
)

User = get_user_model()


@api_view(["POST"])
@permission_classes([AllowAny])
def register(request):
    """Create a new account and return the safe public user representation."""
    serializer = RegisterSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.save()
    return Response(
        UserSerializer(user).data,
        status=status.HTTP_201_CREATED,
    )


# Login: swap in the email-or-username serializer while keeping SimpleJWT's
# TokenObtainPairView (returns {"access": ..., "refresh": ...}).
LoginTokenObtainPairView = TokenObtainPairView.as_view(
    serializer_class=EmailOrUsernameTokenObtainPairSerializer,
)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me(request):
    """Return the authenticated user's safe profile information."""
    return Response(UserSerializer(request.user).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout(request):
    """Invalidate the client-side token session.

    Tokens are stateless (no server blacklist enabled), so logging out simply
    tells the client to discard its access/refresh tokens.
    """
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated])
def profile(request):
    """Read (GET) or safely update (PATCH) the user's own profile."""
    if request.method == "PATCH":
        serializer = ProfileSerializer(
            request.user,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(ProfileSerializer(request.user).data)
    return Response(ProfileSerializer(request.user).data)