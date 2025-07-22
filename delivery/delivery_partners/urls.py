from django.urls import path
from .views import (DeliveryPartnerCreateView,UpdateOrderStatusByPartnerView,DeliveryPartnerDeleteView)

app_name = "deliverypartners"

urlpatterns = [
    path('createpartner/',DeliveryPartnerCreateView.as_view(), name='create-delivery-partner'),
    path('deletepartner/',DeliveryPartnerDeleteView.as_view(),name='delete-delivery-partner'),
    path('updateorderstatus/',UpdateOrderStatusByPartnerView.as_view(),name='update-order-status'),
    
]
