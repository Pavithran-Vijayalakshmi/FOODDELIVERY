from django.urls import path
from . import views
from .views import OrderListCreateView,OrderDetailView


urlpatterns = [
    path('', OrderListCreateView.as_view(), name='order-list-create'),
    path('<int:pk>/', OrderDetailView.as_view(), name='order-detail'),
]