# users/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import user
from .serializer import userSerializer
from rest_framework.response import Response
from rest_framework.permissions import AllowAny,IsAuthenticated
from rest_framework.generics import ListCreateAPIView,RetrieveUpdateDestroyAPIView

class ListUser(ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = userSerializer
    
    def get(self,request):
        queryset = self.get_queryset()
        serializer = self.serializer_class(queryset, many = True)
        return Response(serializer.data)

    def get_queryset(self):
        queryset = user.objects.all()
        name = self.request.query_params.get('name')
        if name:
            queryset = queryset.filter(name=name)  # or use icontains for case-insensitive partial matches
        return queryset
    
class DetailedUser(RetrieveUpdateDestroyAPIView):
    permission_classes = [AllowAny]
    queryset = user.objects.all()
    serializer_class = userSerializer


class currentUserview(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self,request):
        serializer = userSerializer(request.user)
        return Response(serializer.data)