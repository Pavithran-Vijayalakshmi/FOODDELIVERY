from django.urls import path
from . import views
from .views import UserListView

urlpatterns = [
    path('list/', UserListView.as_view(), name='user-list'),
]