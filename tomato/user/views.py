# users/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import userClass
from .serializer import userSerializer
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.permissions import AllowAny

class UserListView(APIView):
    permission_classes = [AllowAny]

    def get_queryset(self):
        return userClass.objects.all()

    def get(self, request):
        users = self.get_queryset()
        serializer = userSerializer(users, many=True)
        return Response(serializer.data)

