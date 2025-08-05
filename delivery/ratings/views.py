from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .models import Rating
from .serializer import RatingSerializer
from common.response import api_response

class RatingCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

        if not (user.user_type == 'customer' or user.is_staff or user.is_superuser):
            return api_response(message= "Only customers can rate items.", status_code=status.HTTP_403_FORBIDDEN)

        data = request.data.copy()

        serializer = RatingSerializer(data=data)

        if serializer.is_valid():
            restaurant_id = data.get('restaurant')
            menu_item_id = data.get('menu_item')

            # Prevent multiple ratings for the same restaurant or menu item
            existing_rating = Rating.objects.filter(
                user=user,
                restaurant_id=restaurant_id if restaurant_id else None,
                menu_item_id=menu_item_id if menu_item_id else None
            ).first()

            if existing_rating:
                return api_response(message= "You have already rated this item.", status_code=status.HTTP_400_BAD_REQUEST)

            # Save the rating with user from token
            serializer.save(user=user)
            return api_response(data=serializer.data, status_code=status.HTTP_201_CREATED)

        return api_response(data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)


class RatingUpdateDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        user = request.user
        rating = Rating.objects.get(user = user)
        
        if not (user.user_type == 'customer' or user.is_staff or user.is_superuser):
            return api_response(message= "Only customers can update ratings.", status_code=status.HTTP_403_FORBIDDEN)

    
        if not rating:
            return api_response(message= 'Rating not found for this user', status_code=status.HTTP_404_NOT_FOUND)

        serializer = RatingSerializer(rating, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return api_response(message= 'Rating updated', data=serializer.data, status_code= status.HTTP_200_OK)
        return api_response(data =  serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        pk = request.query_params.get('rating_id')
        if not pk:
            return api_response(message= 'Rating ID is required', status_code=status.HTTP_400_BAD_REQUEST)

        rating_instance = self.get_object(pk, request.user)
        if not rating_instance:
            return api_response(message= 'Rating not found or not owned by user', status_code=status.HTTP_404_NOT_FOUND)

        rating_instance.delete()
        return api_response(message= 'Rating deleted successfully', status_code=status.HTTP_204_NO_CONTENT)

