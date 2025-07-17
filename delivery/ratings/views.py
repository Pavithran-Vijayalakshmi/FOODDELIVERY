from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .models import rating
from .serializer import RatingSerializer

class RatingCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

        if user.user_type != 'Customer':
            return Response({"error": "Only customers can rate items."}, status=status.HTTP_403_FORBIDDEN)

        data = request.data.copy()

        # You should NOT add 'user' to data — pass it manually to serializer.save()
        serializer = RatingSerializer(data=data)

        if serializer.is_valid():
            restaurant_id = data.get('restaurant')
            menu_item_id = data.get('menu_item')

            # Prevent multiple ratings for the same restaurant or menu item
            existing_rating = rating.objects.filter(
                user=user,
                restaurant_id=restaurant_id if restaurant_id else None,
                menu_item_id=menu_item_id if menu_item_id else None
            ).first()

            if existing_rating:
                return Response({"error": "You have already rated this item."}, status=status.HTTP_400_BAD_REQUEST)

            # Save the rating with user from token
            serializer.save(user=user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RatingUpdateDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk, user):
        try:
            return rating.objects.get(pk=pk, user=user)
        except rating.DoesNotExist:
            return None

    def patch(self, request):
        pk = request.query_params.get('pk')
        if not pk:
            return Response({'error': 'Rating ID (pk) is required'}, status=status.HTTP_400_BAD_REQUEST)

        rating_instance = self.get_object(pk, request.user)
        if not rating_instance:
            return Response({'error': 'Rating not found or not owned by user'}, status=status.HTTP_404_NOT_FOUND)

        serializer = RatingSerializer(rating_instance, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Rating updated', 'data': serializer.data})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        pk = request.query_params.get('pk')
        if not pk:
            return Response({'error': 'Rating ID (pk) is required'}, status=status.HTTP_400_BAD_REQUEST)

        rating_instance = self.get_object(pk, request.user)
        if not rating_instance:
            return Response({'error': 'Rating not found or not owned by user'}, status=status.HTTP_404_NOT_FOUND)

        rating_instance.delete()
        return Response({'message': 'Rating deleted successfully'}, status=status.HTTP_204_NO_CONTENT)

