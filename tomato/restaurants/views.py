# users/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import restaurantsModel, MenuItems, rating,Cart,OrderItems
from .serializer import restaurantsSerializer,MenuItemSerializer,ratingSerializer,CartSerializer,OrderItemSerializer
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets



class restaurantsList(viewsets.ModelViewSet):   
    queryset = restaurantsModel.objects.all()
    serializer_class = restaurantsSerializer
    
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
    
    