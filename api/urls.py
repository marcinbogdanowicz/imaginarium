from django.urls import path, include
from .views import (
    UserDetailView,
    UserListView,
    ImageListUploadView,
    ImageDetailView,
    TempLinkListCreateView,
    TemporaryImageView,
)

urlpatterns = [
    path(
        'auth/',
        include('rest_framework.urls')
    ),
    path(
        'user/',
        UserListView.as_view(),
        name='user-list'
    ),
    path(
        'user/<int:pk>/',
        UserDetailView.as_view(),
        name='user-detail'
    ),
    path(
        'image/',
        ImageListUploadView.as_view(),
        name='image-list-upload'
    ),
    path(
        'image/<int:pk>/',
        ImageDetailView.as_view(),
        name='image-detail'
    ),
    path(
        'image/<int:image_pk>/templink/',
        TempLinkListCreateView.as_view(),
        name='templink-list-create'
    ),
    path(
        'templink/<str:token>/',
        TemporaryImageView.as_view(),
        name='temporary-image-view'
    ),
]