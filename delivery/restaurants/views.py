from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import restaurants, MenuItem
from .serializer import (RestaurantListSerializer, RestaurantDetailSerializer,
                         MenuItemSerializer, RestaurantCreateSerializer, 
                         MenuItemUpdateSerializer, MenuItemCreateSerializer,
                         OfferSerializer)
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticatedOrReadOnly,AllowAny,IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from orders.models import orders
from orders.serializer import OrderSerializer

# Checked

class RestaurantCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.user_type != 'RestaurantOwner':
            return Response({"error": "Only users with 'RestaurantOwner' role can register a restaurant."},
                            status=status.HTTP_403_FORBIDDEN)

        serializer = RestaurantCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(owner=request.user)  # Automatically link restaurant to the user
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    
    
# Checked
class RestaurantListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        queryset = restaurants.objects.all()
        name = request.query_params.get("name")
        is_open = request.query_params.get("is_open")
        category = request.query_params.get("category")
        city = request.query_params.get("city")

        if name:
            queryset = queryset.filter(name__icontains=name)
        if city:
            queryset = queryset.filter(city__icontains=city)
        if is_open is not None:
            queryset = queryset.filter(is_open=is_open.lower() == 'true')
        if category:
            queryset = queryset.filter(menuitem__category__icontains=category).distinct()

        serializer = RestaurantListSerializer(queryset, many=True)
        return Response(serializer.data)


# Checked
class RestaurantDetailView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request):
        id = request.query_params.get("id")
        try:
            restaurant = restaurants.objects.get(id = id)
            
        except restaurants.DoesNotExist:
            return Response({"error": "Restaurant not found"}, status=404)
        serializer = RestaurantDetailSerializer(restaurant)
        return Response(serializer.data)




class MenuCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        restaurant_id = request.data.get('restaurant_id')

        if not restaurant_id:
            return Response({"error": "restaurant_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            restaurant = restaurants.objects.get(id=restaurant_id, owner=user)
        except restaurants.DoesNotExist:
            return Response({"error": "Restaurant not found or not owned by user"}, status=status.HTTP_404_NOT_FOUND)

        serializer = MenuItemCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(restaurant=restaurant)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
# checked
class RestaurantMenuListView(APIView):
    permission_classes = [AllowAny]  # Publicly accessible

    def get(self, request):
        id = request.query_params.get('id')
        category = request.query_params.get('category')
        min_price = request.query_params.get('min_price')
        max_price = request.query_params.get('max_price')

        if not id:
            return Response({"error": "restaurant_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            restaurant = restaurants.objects.get(id=id)
        except restaurants.DoesNotExist:
            return Response({"error": "Restaurant not found"}, status=status.HTTP_404_NOT_FOUND)
        except restaurants.MultipleObjectsReturned:
            return Response({"error": "Multiple restaurants found. Please refine your search (e.g., include city)."}, status=400)

        # Filter menu items
        menu_items = MenuItem.objects.filter(restaurant=restaurant)

        if category:
            menu_items = menu_items.filter(category__iexact=category)

        if min_price:
            try:
                menu_items = menu_items.filter(price__gte=float(min_price))
            except ValueError:
                return Response({"error": "min_price must be a number"}, status=400)

        if max_price:
            try:
                menu_items = menu_items.filter(price__lte=float(max_price))
            except ValueError:
                return Response({"error": "max_price must be a number"}, status=400)

        serializer = MenuItemSerializer(menu_items, many=True)
        return Response({
            "restaurant": restaurant.name,
            "menu": serializer.data
        }, status=status.HTTP_200_OK)


class MenuItemDetailView(APIView):
    def get(self, request, pk):
        item = get_object_or_404(MenuItem, pk=pk)
        serializer = MenuItemSerializer(item)
        return Response(serializer.data)

class MenuItemUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        menu_id = request.query_params.get('id')
        if not menu_id:
            return Response({"error": "Menu item ID is required in query parameters (?id=)"}, status=status.HTTP_400_BAD_REQUEST)

        menu_item = get_object_or_404(MenuItem, id=menu_id)

        # Optional: Ensure the user owns the restaurant before allowing the update
        if menu_item.restaurant.owner != request.user:
            return Response({"error": "You do not have permission to edit this menu item."}, status=status.HTTP_403_FORBIDDEN)

        serializer = MenuItemUpdateSerializer(menu_item, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Menu item updated successfully", "data": serializer.data}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MenuItemDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        menu_item_id = request.query_params.get('id')
        if not menu_item_id:
            return Response({"error": "Menu item ID is required in query parameters (?id=)"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            item = MenuItem.objects.get(id=menu_item_id)
        except MenuItem.DoesNotExist:
            return Response({"error": "Menu item not found."}, status=status.HTTP_404_NOT_FOUND)

        if item.restaurant.owner != request.user :
            raise PermissionDenied("You do not have permission to delete this item.")

        item.delete()
        return Response({"message": "Menu item deleted successfully."}, status=status.HTTP_204_NO_CONTENT)

    
class RestaurantMenuView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        restaurant_name = request.data.get('restaurant_name')

        if not restaurant_name:
            return Response({"error": "restaurant_name is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            restaurant = restaurants.objects.get(name=restaurant_name)
        except restaurants.DoesNotExist:
            return Response({"error": "Restaurant not found"}, status=status.HTTP_404_NOT_FOUND)

        menu = MenuItem.objects.filter(restaurant=restaurant)
        serialized_menu = MenuItemSerializer(menu, many=True)

        return Response({
            "restaurant": restaurant.name,
            "menu": serialized_menu.data
        }, status=status.HTTP_200_OK)
        
        
        

class AllMenuItemsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        if user.user_type != 'Customer':
            return Response({'error': 'Only customers can view menu items.'}, status=status.HTTP_403_FORBIDDEN)

        menu_items = MenuItem.objects.filter(is_available=True).select_related('restaurant')
        serializer = MenuItemSerializer(menu_items, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    

class OfferCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        
        if request.user.user_type != 'RestaurantOwner':
            return Response({"error": "Only restaurant owners can create offers."}, status=status.HTTP_403_FORBIDDEN)

        serializer = OfferSerializer(data=request.data )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    
    
    
class UserRestaurantsListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if user.user_type != 'RestaurantOwner':
            return Response({"error": "Only Restaurant Owners have registered restaurants."}, status=403)

        user_restaurants = restaurants.objects.filter(owner=user)
        serializer = RestaurantDetailSerializer(user_restaurants, many=True)
        return Response(serializer.data)
    
class MarkOrderReadyView(APIView):
    permission_classes = [IsAuthenticated]
    def patch(self, request):
        order_id = request.query_params.get('order_id')
        if not order_id:
            return Response({"error": "Missing 'order_id'"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            order = orders.objects.get(pk=order_id)
        except orders.DoesNotExist:
            return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)

        order.status = 'confirmed'
        order.save()  #Automatically update status

        return Response({"message": "Order marked ready and status set to 'confirmed'"}, status=status.HTTP_200_OK)
