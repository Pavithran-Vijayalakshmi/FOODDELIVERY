from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import User, Favorite, SavedAddress
from .serializer import UserSerializer,UserCreateSerializer, FavoriteSerializer,SavedAddressSerializer, UserProfileUpdateSerializer
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from restaurants.models import Restaurant, MenuItem
from rest_framework.parsers import MultiPartParser, FormParser

class UserListView(APIView):
    
    def get_queryset(self):
        
        return User.objects.all()
    
    def get(self, request):
        users = self.get_queryset()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)
class UserCreateView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = UserCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UpdateUserProfileView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def patch(self, request):
        user = request.user
        serializer = UserProfileUpdateSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
                
            return Response({
                "message": "Profile updated successfully.",
                "data": serializer.data
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    
class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        if user.user_type != 'customer':
            return Response({"error": "Only customers can access this information."}, status=status.HTTP_403_FORBIDDEN)

        serializer = UserSerializer(user)
        return Response(serializer.data)
    
    

    
class FavoriteCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

        if user.user_type != 'customer':
            return Response({"error": "Only customers can create favorites."}, status=403)

        restaurant_id = request.data.get('restaurant_id')   
        menu_item_id = request.data.get('menu_item_id')  

        if restaurant_id and menu_item_id:
            return Response({"error": "Provide either restaurant or menu_item, not both."}, status=400)
        if not restaurant_id and not menu_item_id:
            return Response({"error": "You must provide either restaurant or menu_item as a query parameter."}, status=400)

        if restaurant_id:
            restaurant = get_object_or_404(Restaurant, id=restaurant_id)
            if Favorite.objects.filter(user=user, restaurant=restaurant).exists():
                return Response({"error": "Restaurant already in favorites."}, status=400)
            favorite_obj = Favorite.objects.create(user=user, restaurant=restaurant)

        else:
            menu_item = get_object_or_404(MenuItem, id=menu_item_id)
            if Favorite.objects.filter(user=user, menu_item=menu_item).exists():
                return Response({"error": "Menu item already in favorites."}, status=400)
            favorite_obj = Favorite.objects.create(user=user, menu_item=menu_item)

        serializer = FavoriteSerializer(favorite_obj)
        return Response(serializer.data, status=201)

class FavoriteUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        user = request.user

        if user.user_type != 'customer':
            return Response({"error": "Only customers can update favorites."}, status=403)

        restaurant_id = request.query_params.get('restaurant')
        menu_item_id = request.query_params.get('menu_item')

        # Enforce only one of the two
        if restaurant_id and menu_item_id:
            return Response({"error": "Provide either restaurant or menu_item, not both."}, status=400)
        if not restaurant_id and not menu_item_id:
            return Response({"error": "You must provide either restaurant or menu_item as a query parameter."}, status=400)

        try:
            if restaurant_id:
                favorites = Favorite.objects.get(user=user, restaurant_id=restaurant_id)
            else:
                favorites= Favorite.objects.get(user=user, menu_item_id=menu_item_id)
        except Favorite.DoesNotExist:
            return Response({"error": "Favorite not found."}, status=404)

        # Partial update using PATCH
        serializer = FavoriteSerializer(favorites, data=request.data, partial=True)

        if serializer.is_valid():
            updated_restaurant = serializer.validated_data.get('restaurant')
            updated_menu_item = serializer.validated_data.get('menu_item')

            if updated_restaurant and updated_menu_item:
                return Response({"error": "You can only Favorite either a restaurant or menu item, not both."}, status=400)
            if not updated_restaurant and not updated_menu_item:
                return Response({"error": "At least one of restaurant or menu_item must be provided."}, status=400)

            serializer.save()
            return Response(serializer.data, status=200)

        return Response(serializer.errors, status=400)



class FavoriteDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        user = request.user
        if user.user_type != 'customer':
            return Response({"error": "Only customers can delete favorites."}, status=403)

        restaurant_id = request.query_params.get('restaurant')
        menu_item_id = request.query_params.get('menu_item')

        if restaurant_id and menu_item_id:
            return Response({"error": "Provide either restaurant or menu_item, not both."}, status=400)
        if not restaurant_id and not menu_item_id:
            return Response({"error": "You must provide restaurant or menu_item as query param."}, status=400)

        try:
            if restaurant_id:
                favorites = Favorite.objects.get(user=user, restaurant_id=restaurant_id)
            else:
                favorites = Favorite.objects.get(user=user, menu_item_id=menu_item_id)
        except Favorite.DoesNotExist:
            return Response({"error": "Favorite not found."}, status=404)

        favorites.delete()
        return Response({"message": "Favorite deleted successfully."}, status=204)


class SavedAddressListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if user.user_type != 'customer':
            return Response({'error': 'Only customers can view saved addresses.'}, status=403)

        addresses = SavedAddress.objects.filter(user=user)
        serializer = SavedAddressSerializer(addresses, many=True)
        return Response(serializer.data)

    def post(self, request):
        user = request.user
        if user.user_type != 'customer':
            return Response({'error': 'Only customers can add saved addresses.'}, status=403)

        serializer = SavedAddressSerializer(data=request.data)
        if serializer.is_valid():
            if serializer.validated_data.get('is_default', False):
                SavedAddress.objects.filter(user=user, is_default=True).update(is_default=False)
            serializer.save(user=user)
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)
    
class SavedAddressUpdateDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        user = request.user
        if user.user_type != 'customer':
            return Response({'error': 'Only customers can update addresses.'}, status=403)

        address_id = request.query_params.get('address_id')
        if not address_id:
            return Response({'error': 'address_id is required in query parameters.'}, status=400)

        try:
            address = SavedAddress.objects.get(id=address_id, user=user)
        except SavedAddress.DoesNotExist:
            return Response({'error': 'Address not found.'}, status=404)

        serializer = SavedAddressSerializer(address, data=request.data, partial=True)
        if serializer.is_valid():
            if serializer.validated_data.get('is_default', False):
                SavedAddress.objects.filter(user=user, is_default=True).update(is_default=False)
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    def delete(self, request):
        user = request.user
        if user.user_type != 'customer':
            return Response({'error': 'Only customers can delete addresses.'}, status=403)

        address_id = request.query_params.get('address_id')
        if not address_id:
            return Response({'error': 'address_id is required in query parameters.'}, status=400)

        try:
            address = SavedAddress.objects.get(id=address_id, user=user)
        except SavedAddress.DoesNotExist:
            return Response({'error': 'Address not found.'}, status=404)

        address.delete()
        return Response({'message': 'Deleted successfully.'}, status=204)
