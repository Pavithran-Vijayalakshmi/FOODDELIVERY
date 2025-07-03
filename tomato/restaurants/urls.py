from django.urls import path
from .views import restaurantsList

urlpatterns = [
    path('list/', restaurantsList.as_view(), name='restaurants-list'),
]