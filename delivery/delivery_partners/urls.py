from django.urls import path
from .views import (DeliveryPartnerCreateView,UpdateOrderStatusByPartnerView,
                    DeliveryPartnerListView,DeliveryPartnerDeleteView,
                    DeliveryPersonCreateView,AssignOrderToDeliveryPersonView,
                    DeliveryPersonListView,UpdateDeliveryPersonStatusView,
                    DeliveryPartnerOrderListView)

app_name = "deliverypartners"

urlpatterns = [
    path('createpartner/',DeliveryPartnerCreateView.as_view(), name='create-delivery-partner'),
    path('deletepartner/',DeliveryPartnerDeleteView.as_view(),name='delete-delivery-partner'),
    path('updateorderstatus/',UpdateOrderStatusByPartnerView.as_view(),name='update-order-status'),
    path('listdeliverypartner/',DeliveryPartnerListView.as_view(),name = 'list'),
    path('orderlist/',DeliveryPartnerOrderListView.as_view(),name='confirmed-order-list'),
    
    path('deliveryperson/',DeliveryPersonCreateView.as_view(),name='create-delivery-person'),
    path('listdeliveryperson/',DeliveryPersonListView.as_view(),name = 'list'),
    path('assignorder/',AssignOrderToDeliveryPersonView.as_view(), name='assign-order-to-delivery-person'),
    path('updatedeliverypartner/',UpdateDeliveryPersonStatusView.as_view(), name='updatestatusbydeliverypartner'),
]
