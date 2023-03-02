from django.urls import path
from .views import (
    UserCreateView,
    UserDetailView,
    UserListView,
)

urlpatterns = [
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
]