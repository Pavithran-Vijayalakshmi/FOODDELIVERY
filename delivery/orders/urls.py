from django.urls import path
from .views import (
    CartListView,
    OrderListView,
    CartItemUpdateDeleteView,
    CartCreateView,CancelOrderView,
    OrderCreateView,
    DeleteFinalizedOrdersByOrderCodeView,
    payment_page,
    razorpay_webhook,
)


app_name = "orders"

urlpatterns = [
    path('cart/create/', CartCreateView.as_view(), name='cart-create'),
    path('cart/', CartListView.as_view(), name='cart-list'),
    path('cart/item/update-delete/', CartItemUpdateDeleteView.as_view(), name='cart-item-update'),
    path('razorpay-webhook/', razorpay_webhook, name='razorpay-webhook'),
    path('orderlist/', OrderListView.as_view(), name='order-list'),
    path('deleteorders/',DeleteFinalizedOrdersByOrderCodeView.as_view(),name = 'delete-old-orders'),
    path('create/', OrderCreateView.as_view(), name='create-order'),
    path('cancel/', CancelOrderView.as_view(), name='cancel-order'),    
    path('order/<uuid:order_id>/pay/', payment_page, name='payment-page'),
]
