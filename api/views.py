from django.shortcuts import get_object_or_404
from rest_framework import permissions
from rest_framework.generics import (
    CreateAPIView,
    ListAPIView,
    RetrieveUpdateDestroyAPIView,
)
from .serializers import (
    UserPrivateSerializer,
    UserPublicSerializer,
)
from .models import (
    User
)


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

    queryset = User.objects.all()
    serializer_class = UserPrivateSerializer

    def get_object(self):
        obj = get_object_or_404(User, pk=self.kwargs['user_pk'])
        self.check_object_permissions(self.request, obj)
        return obj


class UserListView(ListAPIView):
    """
    Lists all users. Returns restricted user data.
    Available to all authenticated users.
    """

    queryset = User.objects.all()
    serializer_class = UserPublicSerializer