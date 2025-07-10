from django.urls import path
from . import views
from .views import ListUser,DetailedUser

urlpatterns = [
    path('list/', ListUser.as_view(), name='user-list'),
    path('userdetail/<int:pk>',DetailedUser.as_view(),name = 'User Detail'),
]