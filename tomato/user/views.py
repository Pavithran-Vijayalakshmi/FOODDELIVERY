# users/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import userClass
from .serializer import userSerializer
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.generics import ListCreateAPIView,RetrieveUpdateDestroyAPIView

class ListUser(ListCreateAPIView):
    queryset = userClass.objects.all()
    serializer_class = userSerializer
    
class DetailedUser(RetrieveUpdateDestroyAPIView):
    queryset = userClass.objects.all()
    serializer_class = userSerializer
