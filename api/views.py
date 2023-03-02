from django.shortcuts import get_object_or_404
from rest_framework import permissions
from rest_framework.generics import (
    CreateAPIView,
    ListAPIView,
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
)
from .serializers import (
    UserPrivateSerializer,
    UserPublicSerializer,
    ImageSerializer
)
from .models import (
    User,
    Image
)
from . import permissions as custom_permissions


class UserCreateView(CreateAPIView):
    """
    Create a user instance.
    """

    permission_classes = (permissions.AllowAny,)
    serializer_class = UserPrivateSerializer


class UserDetailView(RetrieveUpdateDestroyAPIView):
    """
    Show, update or delete user instance.
    Available to that user only.
    """

    permission_classes = (custom_permissions.IsOwner,)
    serializer_class = UserPrivateSerializer

    def get_queryset(self):
        user = self.request.user
        return User.objects.filter(pk=user.pk)

    def get_object(self):
        obj = get_object_or_404(self.get_queryset(), pk=self.kwargs['user_pk'])
        self.check_object_permissions(self.request, obj)
        return obj


class UserListView(ListAPIView):
    """
    Lists all users. Returns user public data.
    Available to all authenticated users.
    """

    queryset = User.objects.all()
    serializer_class = UserPublicSerializer


class ImageListUploadView(ListCreateAPIView):
    """
    For users to view lists of their images
    and upload new ones.
    """

    serializer_class = ImageSerializer

    def get_queryset(self):
        # Present only images that belong to requesting user.
        # Present none to guests.
        user = self.request.user
        if user.is_authenticated:
            return Image.objects.filter(owner=user)
        return []