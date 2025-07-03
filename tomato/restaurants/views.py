# users/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import restaurantsModel
from .serializer import restaurantsSerializer
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets


class restaurantsList(viewsets.ModelViewSet):   
    queryset = restaurantsModel.objects.all()
    serializer_class = restaurantsSerializer
    
    