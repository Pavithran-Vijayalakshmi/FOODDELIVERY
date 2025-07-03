# users/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import restaurantsModel
from .serializer import restaurantsSerializer
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

class restaurantsList(APIView):
    permission_classes = [AllowAny]

    def get_queryset(self):
        return restaurantsModel.objects.all()

    def get(self, request):
        hotels = self.get_queryset()
        serializer = restaurantsSerializer(hotels, many=True)
        return Response(serializer.data)

