from django.urls import path
from django.conf.urls.static import static
from delivery.settings import MEDIA_ROOT, MEDIA_URL

from .views import (
    RestaurantListView,
    RestaurantDetailView,
    RestaurantCreateView,
    MenuCreateView,
    MenuItemDetailView,
    MenuItemUpdateDeleteView,
    OfferCreateView,
    UserRestaurantsListView,
    MarkOrderReadyView,
    RestaurantOrderListView,
    RestaurantApprovalView,
    MenuItemApprovalView,
    MenuItemListView
    
)

app_name = "restaurants"

urlpatterns = [
    path('', RestaurantListView.as_view(), name='restaurant-list'),
    path('create/',RestaurantCreateView.as_view(),name = 'restaurant-create'),
    path('approve_restaurant/',RestaurantApprovalView.as_view(), name = 'approve-restaurant'),
    path('approve/menu_item/',MenuItemApprovalView.as_view(),name='approve-menu-item'),
    path('detail/', RestaurantDetailView.as_view(), name='restaurant-detail'),
    path('menu/create/', MenuCreateView.as_view(), name='menu-create'),
    path('menu-items/', MenuItemListView.as_view(), name='menu-items'),
    path('menu-items/details/',MenuItemDetailView.as_view(), name='menu-item-detail'),
    path('menu/update-delete/', MenuItemUpdateDeleteView.as_view(), name='menu-item-update-delete'),
    path('offers/create/', OfferCreateView.as_view(), name='create-offer'),
    path('registered/restaurants/',UserRestaurantsListView.as_view(), name='registered-restaurants' ),
    path('orders/',RestaurantOrderListView.as_view(), name='restaurant-orders'),
    path('orderstatusupdate/',MarkOrderReadyView.as_view(),name='order-status-update'),
    
    
]+ static(MEDIA_URL, document_root=MEDIA_ROOT)
