from django.shortcuts import get_object_or_404
from django.http import FileResponse
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.generics import (
    ListAPIView,
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
)
from rest_framework.views import APIView
from .serializers import (
    UserPrivateSerializer,
    UserPublicSerializer,
    ImageSerializer,
    ImageDetailSerializer,
    TempLinkSerializer,
)
from .models import (
    User,
    Image,
    TempLink,
    TempLinkTokenBlacklist,
)
from . import permissions as custom_permissions


class UserDetailView(RetrieveUpdateDestroyAPIView):
    """
    Show, update or delete user instance.
    Available to that user only.
    """

    permission_classes = (custom_permissions.IsOwner,)
    serializer_class = UserPrivateSerializer
    queryset = User.objects.all()

    def get_object(self):
        obj = get_object_or_404(self.get_queryset(), pk=self.kwargs['pk'])
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
    

class ImageDetailView(RetrieveUpdateDestroyAPIView):
    """
    Shows details of an image. Available for image owner only.
    """

    permission_classes = (custom_permissions.IsOwner,)
    serializer_class = ImageDetailSerializer
    queryset = Image.objects.all()

    def get_object(self):
        obj = get_object_or_404(self.get_queryset(), pk=self.kwargs['pk'])
        self.check_object_permissions(self.request, obj)
        return obj


class TempLinkListCreateView(ListCreateAPIView):
    """
    List and create temporary links. Only for image owner.
    """

    serializer_class = TempLinkSerializer
    permission_classes = (
        permissions.IsAuthenticated,
        custom_permissions.CanCreateTempLinks
    )

    def check_permissions(self, request):
        """
        Perform standard check and also verify if user is the owner
        of the image he creates link to.
        """
        image = get_object_or_404(Image, pk=self.kwargs['image_pk'])
        if request.user != image.owner:
            self.permission_denied(
                    request,
                    message=('Only owners can view and create ' +
                             'temporary links to their images.'),
                    code='Denied'
                )
        return super().check_permissions(request)

    def get_queryset(self):
        image = get_object_or_404(Image, pk=self.kwargs['image_pk'])
        queryset = TempLink.objects.filter(image=image)
        return queryset
    

class TemporaryImageView(APIView):
    """
    Used for temporary links handling. Verifies that link has not expired
    or removes expired one. Returns an image as binary content.
    """

    def get(self, request, token, format=None):
        # Try to find TempLink associated with given URL token.
        try:
            templink = TempLink.objects.get(token=token)
        except TempLink.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        
        # If token has expired, blacklist it and return.
        if templink.has_expired():
            TempLinkTokenBlacklist.objects.create(token=token)
            templink.delete()
            return Response(status=status.HTTP_410_GONE)
        
        # Return image as binary content.
        filename = templink.image.image.path
        return FileResponse(open(filename, 'rb'))


        