from django.urls import path
from .views import UserListView, UserDetailView, MeView,UserCreateView
from restaurants.views import RestaurantMenuView


app_name = "user"

urlpatterns = [
    path('', UserListView.as_view(), name='user-list'),
    path('create/',UserCreateView.as_view(),name= 'user-create'),
    path('<uuid:pk>/', UserDetailView.as_view(), name='user-detail'),
    path('me/', MeView.as_view(), name='user-me'), 
    path('restaurant/menu/', RestaurantMenuView.as_view(), name='restaurant-menu'),
]
