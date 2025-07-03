from rest_framework import generics
from .models import ordersModel
from .serializer import OrdersSerializer

class OrderListCreateView(generics.ListCreateAPIView):
    queryset = ordersModel.objects.all()
    serializer_class = OrdersSerializer

class OrderDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = ordersModel.objects.all()
    serializer_class = OrdersSerializer
