from django.urls import path
from . import views
from .views import ListUser,DetailedUser,currentUserview

urlpatterns = [
    path('list/', ListUser.as_view(), name='user-list'),
    path('me/',currentUserview.as_view(), name = 'me'),
    path('userdetail/<str:email>/', DetailedUser.as_view(), name='user-detail'),
]