# users/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import userClass
from .serializer import userSerializer
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.generics import ListCreateAPIView,RetrieveUpdateDestroyAPIView

class ListUser(ListCreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = userSerializer

    def get_queryset(self):
        queryset = userClass.objects.all()
        name = self.request.query_params.get('name')
        if name:
            queryset = queryset.filter(name=name)  # or use icontains for case-insensitive partial matches
        return queryset
    
class DetailedUser(RetrieveUpdateDestroyAPIView):
    permission_classes = [AllowAny]
    queryset = userClass.objects.all()
    serializer_class = userSerializer
