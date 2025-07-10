# users/views.py
from rest_framework.views import APIView
from rest_framework.generics import ListCreateAPIView,RetrieveUpdateDestroyAPIView
from rest_framework.response import Response
from .models import restaurants, MenuItems, rating,Cart,OrderItems
from .serializer import restaurantsSerializer,MenuItemSerializer,ratingSerializer,CartSerializer,OrderItemSerializer
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets
from rest_framework.permissions import AllowAny



class restaurantsList(ListCreateAPIView):  
    permission_classes = [AllowAny] 
    serializer_class = restaurantsSerializer
    def get_queryset(self):
        queryset = restaurants.objects.all()
        name = self.request.query_params.get("name")
        if name:
            queryset = queryset.filter(name=name)
        return queryset
    
class MenuList(viewsets.ModelViewSet):
    queryset = MenuItems.objects.all()
    serializer_class = MenuItemSerializer

class orderItemsList(viewsets.ModelViewSet):
    queryset = OrderItems.objects.all()
    serializer_class = OrderItemSerializer
    
class CartList(viewsets.ModelViewSet):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer
    
class Ratings(viewsets.ModelViewSet):
    queryset = rating.objects.all()
    serializer_class = ratingSerializer
    
    