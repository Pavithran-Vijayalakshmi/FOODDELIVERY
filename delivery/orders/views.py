from rest_framework import generics
from .models import orders
from .serializer import OrdersSerializer,OrderCartSerializer
from rest_framework.views import  APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

class OrderListCreateView(generics.ListCreateAPIView):
    queryset = orders.objects.all()
    serializer_class = OrdersSerializer

class OrderDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = orders.objects.all()
    serializer_class = OrdersSerializer

class CartView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        serializer = OrderCartSerializer(data = request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Added to Cart"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status = status.HTTP_400_BAD_REQUEST)