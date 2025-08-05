from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import User, Favorite, SavedAddress
from .serializer import (UserSerializer,UserCreateSerializer,
                         FavoriteSerializer,SavedAddressSerializer, 
                         UserProfileUpdateSerializer,
                         AdminUserCreateSerializer,AdminUserSerializer,
                         RestaurantDetailSerializer)
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from restaurants.models import Restaurant, MenuItem
from rest_framework.parsers import MultiPartParser, FormParser
from common.response import api_response
from django.db.models import Q


class AdminUserListView(APIView):
    permission_classes = [IsAdminUser]
    
    def get(self, request):
        users = User.objects.all()
        serializer = AdminUserSerializer(users, many=True)
        return api_response(data=serializer.data, status_code=status.HTTP_200_OK)

class AdminUserCreateView(APIView):
    permission_classes = [IsAdminUser]
    
    def post(self, request):
        serializer = AdminUserCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return api_response(
                data=serializer.data, 
                status_code=status.HTTP_201_CREATED
            )
        return api_response(
            data=serializer.errors, 
            status_code=status.HTTP_400_BAD_REQUEST
        )

class UserListCreateView(APIView):
    permission_classes = [IsAdminUser]
    
    def get_queryset(self):
        return User.objects.all()
    
    def get(self, request):
        users = self.get_queryset()
        serializer = UserSerializer(users, many=True)
        return api_response(status_code=status.HTTP_200_OK,data=serializer.data)
    
    
    def post(self, request):
        serializer = UserCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return api_response(data=serializer.data, status_code=status.HTTP_201_CREATED)
        return api_response(data=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    
    

class UpdateUserProfileView(APIView):
    permission_classes = [IsAuthenticated]
    # parser_classes = [MultiPartParser, FormParser]
    
    def patch(self, request):
        user = request.user
        if not (user.user_type == 'customer' or user.is_staff or user.is_superuser):
            return api_response(message="Only customers or admin can update the profile",
                             status_code=status.HTTP_403_FORBIDDEN)
        data = request.data
        serializer = UserProfileUpdateSerializer(user, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
                
            return api_response(
                message="Profile updated successfully.",
                data= serializer.data,
                
                status_code=status.HTTP_200_OK
            )
        return api_response(data=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    
    
class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        if not (user.user_type == 'customer' or user.is_staff or user.is_superuser):
            return api_response(data="Only customers can access this information.", status_code=status.HTTP_403_FORBIDDEN)

        serializer = UserSerializer(user)
        return api_response(data=serializer.data, status_code=status.HTTP_200_OK)
    
    

    
class FavoriteCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

        if not (user.user_type == 'customer' or user.is_staff or user.is_superuser):
            return api_response(data= "Only customers can create favorites.", status_code=status.HTTP_403_FORBIDDEN)

        restaurant_id = request.data.get('restaurant_id')   
        menu_item_id = request.data.get('menu_item_id')  

        if restaurant_id and menu_item_id:
            return api_response(data= "Provide either restaurant or menu_item, not both.", status_code=status.HTTP_400_BAD_REQUEST)
        if not restaurant_id and not menu_item_id:
            return api_response(data= "You must provide either restaurant or menu_item as a query parameter.", status_code=status.HTTP_400_BAD_REQUEST)

        if restaurant_id:
            restaurant = get_object_or_404(Restaurant, id=restaurant_id)
            if Favorite.objects.filter(user=user, restaurant=restaurant).exists():
                return api_response(data="Restaurant already in favorites.", status_code=status.HTTP_400_BAD_REQUEST)
            
            favorite_obj = Favorite.objects.create(user=user, restaurant=restaurant)

        else:
            menu_item = get_object_or_404(MenuItem, id=menu_item_id)
            if Favorite.objects.filter(user=user, menu_item=menu_item).exists():
                return api_response(data= "Menu item already in favorites.", status_code=status.HTTP_400_BAD_REQUEST)
            favorite_obj = Favorite.objects.create(user=user, menu_item=menu_item)

        serializer = FavoriteSerializer(favorite_obj)
        return api_response(data = serializer.data, status_code=status.HTTP_201_CREATED)

class FavoriteUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        user = request.user

        if not (user.user_type == 'customer' or user.is_staff or user.is_superuser):
            return api_response(data= "Only customers can update favorites.", status_code=status.HTTP_403_FORBIDDEN)

        restaurant_id = request.query_params.get('restaurant')
        menu_item_id = request.query_params.get('menu_item')

        # Enforce only one of the two
        if restaurant_id and menu_item_id:
            return api_response(data= "Provide either restaurant or menu_item, not both.", status_code=status.HTTP_400_BAD_REQUEST)
        if not restaurant_id and not menu_item_id:
            return api_response(data= "You must provide either restaurant or menu_item as a query parameter.", status_code=status.HTTP_400_BAD_REQUEST)

        try:
            if restaurant_id:
                favorites = Favorite.objects.get(user=user, restaurant_id=restaurant_id)
            else:
                favorites= Favorite.objects.get(user=user, menu_item_id=menu_item_id)
        except Favorite.DoesNotExist:
            return api_response(data= "Favorite not found.", status_code=status.HTTP_404_NOT_FOUND)

        # Partial update using PATCH
        serializer = FavoriteSerializer(favorites, data=request.data, partial=True)

        if serializer.is_valid():
            updated_restaurant = serializer.validated_data.get('restaurant')
            updated_menu_item = serializer.validated_data.get('menu_item')

            if updated_restaurant and updated_menu_item:
                return api_response(data= "You can only Favorite either a restaurant or menu item, not both.", status_code=status.HTTP_400_BAD_REQUEST)
            if not updated_restaurant and not updated_menu_item:
                return api_response(data= "At least one of restaurant or menu_item must be provided.", status_code=status.HTTP_400_BAD_REQUEST)

            serializer.save()
            return api_response(data = serializer.data, status_code=status.HTTP_200_OK)

        return api_response(data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)



class FavoriteDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        user = request.user
        if not (user.user_type == 'customer' or user.is_staff or user.is_superuser):
            return api_response(data= "Only customers can delete favorites.", status_code=status.HTTP_400_BAD_REQUEST)

        restaurant_id = request.query_params.get('restaurant')
        menu_item_id = request.query_params.get('menu_item')

        if restaurant_id and menu_item_id:
            return api_response(data= "Provide either restaurant or menu_item, not both.", status_code=status.HTTP_400_BAD_REQUEST)
        if not restaurant_id and not menu_item_id:
            return api_response(data= "You must provide restaurant or menu_item as query param.", status_code=status.HTTP_400_BAD_REQUEST)

        try:
            if restaurant_id:
                favorites = Favorite.objects.get(user=user, restaurant_id=restaurant_id)
            else:
                favorites = Favorite.objects.get(user=user, menu_item_id=menu_item_id)
        except Favorite.DoesNotExist:
            return api_response(data= "Favorite not found.", status_code=status.HTTP_404_NOT_FOUND)

        favorites.delete()
        return api_response(data= "Favorite deleted successfully.", status_code=status.HTTP_204_NO_CONTENT)


class SavedAddressListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if not (user.user_type == 'customer' or user.is_staff or user.is_superuser):
            return api_response(data= 'Only customers or admin can view saved addresses.', status_code=status.HTTP_400_BAD_REQUEST)

        addresses = SavedAddress.objects.filter(user=user)
        serializer = SavedAddressSerializer(addresses, many=True)
        return api_response(data = serializer.data)

    def post(self, request):
        user = request.user
        if not (user.user_type == 'customer' or user.is_staff or user.is_superuser):
            return api_response(
                data={'message': 'Only customers can add saved addresses.'},
                status_code=status.HTTP_403_FORBIDDEN
            )

        serializer = SavedAddressSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if not serializer.is_valid():
            return api_response(
                data=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )

        # Handle default address logic
        if serializer.validated_data.get('is_default', False):
            SavedAddress.objects.filter(
                user=user, 
                is_default=True
            ).update(is_default=False)
        
        serializer.save()
        return api_response(
            data=serializer.data,
            status_code=status.HTTP_201_CREATED
        )
    
class SavedAddressUpdateDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        user = request.user
        if not (user.user_type == 'customer' or user.is_staff or user.is_superuser):
            return api_response(data= 'Only customers or admin can update addresses.', status_code=status.HTTP_400_BAD_REQUEST)

        address_id = request.query_params.get('address_id')
        if not address_id:
            return api_response(data= 'address_id is required in query parameters.', status_code=status.HTTP_400_BAD_REQUEST)

        try:
            address = SavedAddress.objects.get(id=address_id, user=user)
        except SavedAddress.DoesNotExist:
            return api_response(data= 'Address not found.', status_code=status.HTTP_404_NOT_FOUND)

        serializer = SavedAddressSerializer(address, data=request.data, partial=True)
        if serializer.is_valid():
            if serializer.validated_data.get('is_default', False):
                SavedAddress.objects.filter(user=user, is_default=True).update(is_default=False)
            serializer.save()
            return api_response(data = serializer.data, status_code=status.HTTP_200_OK)
        return api_response(data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        user = request.user
        if not (user.user_type == 'customer' or user.is_staff or user.is_superuser):
            return api_response(data= 'Only customers can delete addresses.', status_code=status.HTTP_400_BAD_REQUEST)

        address_id = request.query_params.get('address_id')
        if not address_id:
            return api_response(data= 'address_id is required in query parameters.', status_code=status.HTTP_400_BAD_REQUEST)

        try:
            address = SavedAddress.objects.get(id=address_id, user=user)
        except SavedAddress.DoesNotExist:
            return api_response(data= 'Address not found.', status_code=status.HTTP_404_NOT_FOUND)

        address.delete()
        return api_response(data= 'Deleted successfully.', status_code=status.HTTP_204_NO_CONTENT)



class RestaurantListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        
        queryset = Restaurant.objects.select_related(
            'city', 
            'city__state',
        ).filter(is_approved=True)  

        # Get filter parameters
        name = request.query_params.get("name")
        is_open = request.query_params.get("is_open")
        category = request.query_params.get("category")
        city = request.query_params.get("city")
        restaurant_type = request.query_params.get("type")

        # Apply filters
        if name:
            queryset = queryset.filter(
                Q(name__icontains=name) | 
                Q(description__icontains=name)
            )
        if city:
            queryset = queryset.filter(city__name__icontains=city)
        if is_open is not None:
            queryset = queryset.filter(is_open=is_open.lower() == 'true')
        if category:
            queryset = queryset.filter(
                Q(menu_items__category__name__icontains=category) |
                Q(restaurant_type__icontains=category)
            ).distinct()
        if restaurant_type:
            queryset = queryset.filter(restaurant_type__iexact=restaurant_type)

        # Add pagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = RestaurantDetailSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = RestaurantDetailSerializer(queryset, many=True)
        
        return api_response(
            data=serializer.data, 
            status_code=status.HTTP_200_OK
        ) if serializer.data else api_response(
            data={"message": "No restaurants found matching your criteria"},
            status_code=status.HTTP_404_NOT_FOUND
        )

    # Pagination support
    @property
    def paginator(self):
        if not hasattr(self, '_paginator'):
            from rest_framework.pagination import PageNumberPagination
            self._paginator = PageNumberPagination()
            self._paginator.page_size = 10  # Default page size
        return self._paginator

    def paginate_queryset(self, queryset):
        if 'page' in self.request.query_params:
            return self.paginator.paginate_queryset(
                queryset, 
                self.request, 
                view=self
            )
        return None

    def get_paginated_response(self, data):
        return self.paginator.get_paginated_response(data)