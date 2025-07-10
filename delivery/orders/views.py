from rest_framework import generics
from .models import orders
from .serializer import OrdersSerializer


class OrderListCreateView(generics.ListCreateAPIView):
    queryset = orders.objects.all()
    serializer_class = OrdersSerializer

class OrderDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = orders.objects.all()
    serializer_class = OrdersSerializer


