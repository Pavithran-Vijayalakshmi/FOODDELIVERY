from django.urls import path
from .views import (
    CartListView,
    OrderListView, OrderDetailView,
    OrderItemListCreateView, OrderItemDetailView,
    CartItemDeleteView, CartItemUpdateView,
    CartCreateView,CancelOrderView,
    OrderCreateView
)

app_name = "orders"

urlpatterns = [
    path('cart/create/', CartCreateView.as_view(), name='cart-create'),
    path('cart/', CartListView.as_view(), name='cart-list'),
    path('cart/item/update/', CartItemUpdateView.as_view(), name='cart-item-update'),
    path('cart/item/delete/', CartItemDeleteView.as_view(), name='cart-item-delete'),
    
    path('orderlist/', OrderListView.as_view(), name='order-list'),
    path('create/', OrderCreateView.as_view(), name='cancel-order'),
    path('cancel/', CancelOrderView.as_view(), name='cancel-order'),
]
