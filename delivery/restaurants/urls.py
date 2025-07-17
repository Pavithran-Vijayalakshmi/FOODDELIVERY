from django.urls import path
from .views import (
    RestaurantListView,
    RestaurantDetailView,
    RestaurantCreateView,
    MenuCreateView,
    RestaurantMenuListView,
    MenuItemDetailView,
    MenuItemDeleteView,
    MenuItemUpdateView,
    OfferCreateView,
)

app_name = "restaurants"

urlpatterns = [
    path('', RestaurantListView.as_view(), name='restaurant-list'),
    path('register/',RestaurantCreateView.as_view(),name = 'restaurant-create'),
    path('detail/', RestaurantDetailView.as_view(), name='restaurant-detail'),
    path('menu/create/', MenuCreateView.as_view(), name='menu-create'),
    path('menu-items/', RestaurantMenuListView.as_view(), name='restaurant-menu-items'),
    path('menu-items/details/',MenuItemDetailView.as_view(), name='menu-item-detail'),
    path('menu/update/', MenuItemUpdateView.as_view(), name='menu-item-update'),
    path('menu/delete/', MenuItemDeleteView.as_view(), name='menu-item-delete'),
    path('offers/create/', OfferCreateView.as_view(), name='create-offer'),
]
