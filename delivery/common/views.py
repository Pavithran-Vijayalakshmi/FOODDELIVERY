from .response import api_response
from .models import Region
from rest_framework.views import APIView
from .serializer import RegionSerializer
from rest_framework import status
from rest_framework.permissions import AllowAny

class RegionListView(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        regions = Region.objects.all()
        serializer = RegionSerializer(regions, many=True)
        return api_response(data = serializer.data, status_code= status.HTTP_200_OK)

