from django.urls import path, include
from .views import (
    UserCreateView,
    UserDetailView,
    UserListView,
    ImageListUploadView,
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
        'user/create/',
        UserCreateView.as_view(),
        name='user-create'
    ),
    path(
        'user/<int:user_pk>/',
        UserDetailView.as_view(),
        name='user-detail'
    ),
    path(
        'image/',
        ImageListUploadView.as_view(),
        name='image-list-upload'
    ),
]