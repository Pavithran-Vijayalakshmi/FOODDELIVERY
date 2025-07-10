from django.urls import path
from . import views
from .views import OrderListCreateView,OrderDetailView

app_name = 'orders'

urlpatterns = [
    path('', OrderListCreateView.as_view(), name='order-list'),
    path('<int:pk>/', OrderDetailView.as_view(), name='order-detail'),
]