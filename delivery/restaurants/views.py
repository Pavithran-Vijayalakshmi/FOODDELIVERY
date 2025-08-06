from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Restaurant, MenuItem, Offer
from .serializer import (RestaurantListSerializer, RestaurantDetailSerializer,
                         MenuItemSerializer, RestaurantCreateSerializer, 
                         MenuItemUpdateSerializer, MenuItemCreateSerializer,
                         OfferSerializer, RestaurantUpdateSerializer)
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticatedOrReadOnly,AllowAny,IsAuthenticated, IsAdminUser, DjangoModelPermissions
from rest_framework.exceptions import PermissionDenied
from rest_framework.parsers import MultiPartParser, JSONParser
from orders.models import Orders
from orders.serializer import OrderSerializer
from django.db.models import Max, Q
from common.response import api_response
from django.core.files.images import get_image_dimensions
from delivery.settings import IMAGE_MAX_HEIGHT, IMAGE_MAX_WIDTH
from django.db import transaction

class RestaurantApprovalView(APIView):
    permission_classes = [IsAuthenticated, DjangoModelPermissions]
    
    def get_queryset(self):
        return Restaurant.objects.all()  
    
    def post(self, request):
        try:
            restaurant_id = request.data.get('restaurant_id')
            restaurant = Restaurant.objects.get(id=restaurant_id)
        except Restaurant.DoesNotExist:
            return api_response(
                data={"detail": "Restaurant not found"},
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # Check if user has approval permission
        if not request.user.has_perm('restaurants.can_approve_restaurant'):
            return api_response(
                data={"detail": "You don't have permission to approve restaurants"},
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        restaurant.is_approved = True
        restaurant.save()

        return api_response(
            data=RestaurantDetailSerializer(restaurant).data,
            status_code=status.HTTP_200_OK
        )

class MenuItemApprovalView(APIView):
    permission_classes = [IsAuthenticated, DjangoModelPermissions]    
    def get_queryset(self):
        return Restaurant.objects.all()  
    
    def post(self, request):
        try:
            menu_item_id = request.data.get('id')
            menuitem = MenuItem.objects.get(id=menu_item_id)
        except MenuItem.DoesNotExist:
            return api_response(
                data={"detail": "Menu Item not found"},
                status_code=status.HTTP_404_NOT_FOUND
            )

        if not request.user.has_perm('restaurants.can_approve_restaurant'):
            return api_response(
                data={"detail": "You don't have permission to approve restaurants"},
                status_code=status.HTTP_403_FORBIDDEN
            )

        menuitem.is_approved = True
        menuitem.save()

        return api_response(
            data=MenuItemCreateSerializer(menuitem).data,
            status_code=status.HTTP_200_OK
        )

class RestaurantCreateView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser]

    def post(self, request):
        if not (request.user.user_type == 'restaurant_owner' or request.user.is_staff or request.user.is_superuser):
            return api_response(
                data="Only restaurant owners or staff can register a restaurant.",
                status_code=status.HTTP_403_FORBIDDEN
            )

        serializer = RestaurantCreateSerializer(data=request.data,context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return api_response(
                data={
                    "message": "Restaurant created successfully. Waiting for Admin Approval",
                    "restaurant": serializer.data
                },
                status_code=status.HTTP_201_CREATED
            )
        return api_response(data=serializer.errors,status_code=status.HTTP_400_BAD_REQUEST)
    


class RestaurantListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = Restaurant.objects.all()
        print(queryset)
        
        if not (request.user.is_staff or request.user.is_superuser):
            queryset = queryset.filter(is_approved=True)

        # Get filter parameters
        name = request.query_params.get("name")
        is_open = request.query_params.get("is_open")
        category = request.query_params.get("category")
        city = request.query_params.get("city")
        restaurant_type = request.query_params.get("type")

        # Apply filters
        if name:
            queryset = queryset.filter(Q(name__icontains=name) | Q(description__icontains=name))
        if city:
            queryset = queryset.filter(city__name__icontains=city)
        if is_open is not None:
            queryset = queryset.filter(is_open=is_open.lower() == 'true')
        if category:
            queryset = queryset.filter(Q(menu_items__category__name__icontains=category) | Q(restaurant_type__icontains=category)).distinct()
        if restaurant_type:
            queryset = queryset.filter(restaurant_type__iexact=restaurant_type)

        # Add pagination
        page = self.paginate_queryset(queryset)
        
        # Choose serializer based on user type
        if request.user.is_staff or request.user.is_superuser:
            serializer_class = RestaurantDetailSerializer
        else:
            serializer_class = RestaurantListSerializer

        if page is not None:
            serializer = serializer_class(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = serializer_class(queryset, many=True)
        print(serializer.data)
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

# Checked
class RestaurantDetailView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request):
        id = request.query_params.get("id")
        try:
            restaurant = Restaurant.objects.get(id = id)
            
        except Restaurant.DoesNotExist:
            return api_response(data= "Restaurant not found", status_code=404)
        serializer = RestaurantDetailSerializer(restaurant)
        return api_response(data=serializer.data, status_code=status.HTTP_200_OK) if serializer.data else api_response(status_code=status.HTTP_404_NOT_FOUND)

# class RestaurantUpdateDeleteView(APIView):
#     permission_classes = [IsAuthenticated]

#     def patch(self, request):
#         user = request.user
#         # Check if user has permission to update restaurants
#         if not (user.user_type == 'restaurant_owner' or user.is_staff or user.is_superuser):
#             return api_response(
#                 message="Only restaurant owners or admin can update restaurants",
#                 status_code=status.HTTP_403_FORBIDDEN
#             )
            
#         restaurant_id = request.query_params.get('id')
#         if not restaurant_id:
#             return api_response(
#                 data="Restaurant ID is required in query parameters (?id=)",
#                 status_code=status.HTTP_400_BAD_REQUEST
#             )

#         restaurant = get_object_or_404(Restaurant, id=restaurant_id)

#         # Additional permission check - only owner or admin can update
#         if not (request.user.is_staff or request.user.is_superuser or restaurant.owner == request.user):
#             return api_response(
#                 data="You don't have permission to update this restaurant",
#                 status_code=status.HTTP_403_FORBIDDEN
#             )

#         serializer = RestaurantDetailSerializer(restaurant, data=request.data, partial=True)
#         if serializer.is_valid():
#             serializer.save()
#             return api_response(
#                 message="Restaurant updated successfully",
#                 data=serializer.data,
#                 status_code=status.HTTP_200_OK
#             )

#         return api_response(
#             data=serializer.errors,
#             status_code=status.HTTP_400_BAD_REQUEST
#         )
    
#     def delete(self, request):
#         user = request.user
#         if not (user.user_type == 'restaurant_owner' or user.is_staff or user.is_superuser):
#             return api_response(
#                 message="Only restaurant owners or admin can delete restaurants",
#                 status_code=status.HTTP_403_FORBIDDEN
#             )
            
#         restaurant_id = request.query_params.get('id')
#         if not restaurant_id:
#             return api_response(
#                 data="Restaurant ID is required in query parameters (?id=)",
#                 status_code=status.HTTP_400_BAD_REQUEST
#             )

#         try:
#             restaurant = Restaurant.objects.get(id=restaurant_id)
#         except Restaurant.DoesNotExist:
#             return api_response(
#                 data="Restaurant not found",
#                 status_code=status.HTTP_404_NOT_FOUND
#             )

#         # Check if user is owner or admin
#         if not (request.user.is_staff or request.user.is_superuser or restaurant.owner == request.user):
#             return api_response(
#                 data="You don't have permission to delete this restaurant",
#                 status_code=status.HTTP_403_FORBIDDEN
#             )

#         # Optional: Check if restaurant has active orders before deletion
#         if restaurant.orders.filter(status__in=['pending', 'out_for_delivery']).exists():
#             return api_response(
#                 message="Cannot delete restaurant with active orders",
#                 status_code=status.HTTP_400_BAD_REQUEST
#             )

#         restaurant.delete()
#         return api_response(
#             message="Restaurant deleted successfully",
#             status_code=status.HTTP_204_NO_CONTENT
#         )

# In views.py
class RestaurantUpdateDeleteView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, JSONParser]  # For handling file uploads

    def patch(self, request):
        user = request.user
        # Check if user has permission to update restaurants
        if not (user.user_type == 'restaurant_owner' or user.is_staff or user.is_superuser):
            return api_response(
                message="Only restaurant owners or admin can update restaurants",
                status_code=status.HTTP_403_FORBIDDEN
            )
            
        restaurant_id = request.query_params.get('id')
        if not restaurant_id:
            return api_response(
                data="Restaurant ID is required in query parameters (?id=)",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        restaurant = get_object_or_404(Restaurant, id=restaurant_id)

        # Additional permission check - only owner or admin can update
        if not (request.user.is_staff or request.user.is_superuser or restaurant.owner == request.user):
            return api_response(
                data="You don't have permission to update this restaurant",
                status_code=status.HTTP_403_FORBIDDEN
            )
        data = request.data.dict() if hasattr(request.data, 'dict') else request.data
        serializer = RestaurantUpdateSerializer(
            restaurant, 
            data=data, 
            partial=True,
            context={'request': request}
        )
        
        if serializer.is_valid():
            with transaction.atomic():
                restaurant = serializer.save()
                
                # If sensitive fields were updated, notify admin
                sensitive_fields = [
                    'pan_card', 'gst_number', 'fssai_license',
                    'account_holder_name', 'account_number', 'ifsc_code', 
                    'bank_name', 'upi_id'
                ]
                
                if any(field in serializer.validated_data for field in sensitive_fields):
                    # notify_admin_about_restaurant_update(restaurant)
                    
                    return api_response(
                        message="Restaurant updated successfully. Changes to sensitive fields require admin approval.",
                        data=serializer.data,
                        status_code=status.HTTP_200_OK
                    )
                
            return api_response(
                message="Restaurant updated successfully",
                data=serializer.data,
                status_code=status.HTTP_200_OK
            )

        return api_response(
            data=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    def delete(self, request):
        user = request.user
        if not (user.user_type == 'restaurant_owner' or user.is_staff or user.is_superuser):
            return api_response(
                message="Only restaurant owners or admin can delete restaurants",
                status_code=status.HTTP_403_FORBIDDEN
            )
            
        restaurant_id = request.query_params.get('id')
        if not restaurant_id:
            return api_response(
                data="Restaurant ID is required in query parameters (?id=)",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        try:
            restaurant = Restaurant.objects.get(id=restaurant_id)
        except Restaurant.DoesNotExist:
            return api_response(
                data="Restaurant not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        # Check if user is owner or admin
        if not (request.user.is_staff or request.user.is_superuser or restaurant.owner == request.user):
            return api_response(
                data="You don't have permission to delete this restaurant",
                status_code=status.HTTP_403_FORBIDDEN
            )

        # Optional: Check if restaurant has active orders before deletion
        if restaurant.orders.filter(status__in=['pending', 'out_for_delivery']).exists():
            return api_response(
                message="Cannot delete restaurant with active orders",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        # Delete related menu items and offers
        MenuItem.objects.filter(restaurant=restaurant).delete()
        Offer.objects.filter(restaurant=restaurant).delete()
        
        restaurant.delete()
        return api_response(
            message="Restaurant and all related data deleted successfully",
            status_code=status.HTTP_204_NO_CONTENT
        )


class MenuCreateView(APIView):
    permission_classes = [IsAuthenticated]
    
    @transaction.atomic
    def post(self, request):
        user = request.user
        restaurant_id = request.data.get('restaurant_id')
        name = request.data.get('name')
        
        # Image validation
        image = request.FILES.get('image')
        if image:
            try:
                width, height = get_image_dimensions(image)
                if width > IMAGE_MAX_WIDTH or height > IMAGE_MAX_HEIGHT:
                    return api_response(
                        data=f"Image dimensions must be under {IMAGE_MAX_WIDTH}x{IMAGE_MAX_HEIGHT}",
                        status_code=status.HTTP_400_BAD_REQUEST
                    )
                    
                # Validate image content type
                if image.content_type not in ['image/jpeg', 'image/png', 'image/webp']:
                    return api_response(
                        data="Only JPEG, PNG, or WebP images are allowed",
                        status_code=status.HTTP_400_BAD_REQUEST
                    )
                    
            except (AttributeError, TypeError):
                return api_response(
                    data="Invalid image file",
                    status_code=status.HTTP_400_BAD_REQUEST
                )
        
        # Validate required fields
        if not restaurant_id:
            return api_response(
                data={"restaurant_id": "This field is required"},
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        if not name:
            return api_response(
                data={"name": "This field is required"},
                status_code=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Get restaurant with optimization
            restaurant = Restaurant.objects.select_related('owner').get(id=restaurant_id)
            
            # Authorization check
            if not (user.is_staff or user.is_superuser or restaurant.owner == user):
                return api_response(
                    data="You don't have permission to add menus to this restaurant",
                    status_code=status.HTTP_403_FORBIDDEN
                )
                
            if restaurant.owner == user and not restaurant.is_approved:
                return api_response(
                    message='Your restaurant is not yet approved',
                    status_code=status.HTTP_403_FORBIDDEN
                )
                
        except Restaurant.DoesNotExist:
            return api_response(
                data="Restaurant not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # Check for duplicate menu item
        if MenuItem.objects.filter(name=name, restaurant=restaurant).exists():
            return api_response(
                data=f"Menu item '{name}' already exists for this restaurant",
                status_code=status.HTTP_409_CONFLICT
            )
        
        
        
        # Create menu item
        serializer = MenuItemCreateSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            serializer.save(restaurant=restaurant)
            return api_response(
                data=serializer.data,
                message="Menu item created successfully",
                status_code=status.HTTP_201_CREATED
            )
            
        return api_response(
            data=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
# checked
class RestaurantMenuListView(APIView):
    permission_classes = [AllowAny] 

    def get(self, request):
        id = request.query_params.get('id')
        category = request.query_params.get('category')
        min_price = request.query_params.get('min_price')
        max_price = request.query_params.get('max_price')

        if not id:
            return api_response(data= "restaurant_id is required", status_code=status.HTTP_400_BAD_REQUEST)

        try:
            restaurant = Restaurant.objects.get(id=id)
        except Restaurant.DoesNotExist:
            return api_response(data= "Restaurant not found", status_code=status.HTTP_404_NOT_FOUND)
        except Restaurant.MultipleObjectsReturned:
            return api_response(data= "Multiple Restaurant found. Please refine your search (e.g., include city).", status_code=400)

        # Filter menu items
        menu_items = MenuItem.objects.filter(restaurant=restaurant)

        if category:
            menu_items = menu_items.filter(category__iexact=category)

        if min_price:
            try:
                menu_items = menu_items.filter(price__gte=float(min_price))
            except ValueError:
                return api_response(data= "min_price must be a number", status_code=400)

        if max_price:
            try:
                menu_items = menu_items.filter(price__lte=float(max_price))
            except ValueError:
                return api_response(data= "max_price must be a number", status_code=400)

        serializer = MenuItemSerializer(menu_items, many=True)
        return api_response(data = {
            "restaurant": restaurant.name,
            "menu": serializer.data}
        , status_code=status.HTTP_200_OK)


class MenuItemDetailView(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        id = request.query_params.get('id')
        item = get_object_or_404(MenuItem, id = id)
        serializer = MenuItemSerializer(item)
        return api_response(data=serializer.data, status_code=status.HTTP_200_OK) if serializer.data else api_response(status_code=status.HTTP_404_NOT_FOUND)


class MenuItemUpdateDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        user = request.user
        if not( user.user_type == 'restaurant_owner' or user.is_staff or user.is_superuser):
            return api_response(message = "Only owners or admin update menu items", 
                          status_code=status.HTTP_403_FORBIDDEN)
            
        menu_id = request.query_params.get('id')
        if not menu_id:
            return api_response(data= "Menu item ID is required in query parameters (?id=)", status_code=status.HTTP_400_BAD_REQUEST)

        menu_item = get_object_or_404(MenuItem, id=menu_id)

        if not (request.user.is_staff or request.user.is_superuser or menu_item.restaurant.owner == request.user):
            return api_response(data="You don't have permission", status_code=403)

        serializer = MenuItemUpdateSerializer(menu_item, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return api_response(message= "Menu item updated successfully", data= serializer.data, status_code=status.HTTP_200_OK)

        return api_response(data=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request):
        user = request.user
        if not( user.user_type == 'restaurant_owner' or user.is_staff or user.is_superuser):
            return api_response(message = "Only owners or admin delete menu items", 
                          status_code=status.HTTP_403_FORBIDDEN)
        menu_item_id = request.query_params.get('id')
        if not menu_item_id:
            return api_response(data= "Menu item ID is required in query parameters (?id=)", status_code=status.HTTP_400_BAD_REQUEST)

        try:
            item = MenuItem.objects.get(id=menu_item_id)
        except MenuItem.DoesNotExist:
            return api_response(data= "Menu item not found.", status_code=status.HTTP_404_NOT_FOUND)

        if not (request.user.is_staff or request.user.is_superuser) or item.restaurant.owner != request.user :
            raise PermissionDenied("You do not have permission to delete this item.")

        item.delete()
        return api_response(message= "Menu item deleted successfully.", status_code=status.HTTP_204_NO_CONTENT)


    
class RestaurantMenuView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        restaurant_name = request.data.get('restaurant_name')

        if not restaurant_name:
            return api_response(data= "restaurant_name is required", status_code=status.HTTP_400_BAD_REQUEST)

        try:
            restaurant = Restaurant.objects.get(name=restaurant_name)
        except Restaurant.DoesNotExist:
            return api_response(data= "Restaurant not found", status_code=status.HTTP_404_NOT_FOUND)

        menu = MenuItem.objects.filter(restaurant=restaurant)
        serialized_menu = MenuItemSerializer(menu, many=True)

        return api_response(data = {
            "restaurant": restaurant.name,
            "menu": serialized_menu.data}
        , status_code=status.HTTP_200_OK)
        
        
        


    
    


    
    
    
class UserRestaurantsListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if not (user.user_type == 'restaurant_owner' or request.user.is_staff or request.user.is_superuser):
            return api_response(data= "Only Restaurant Owners have registered Restaurant.", status_code=403)

        user_restaurants = Restaurant.objects.filter(owner=user)
        serializer = RestaurantDetailSerializer(user_restaurants, many=True)
        
        return api_response(data=serializer.data, status_code=status.HTTP_200_OK) if serializer.data else api_response(status_code=status.HTTP_404_NOT_FOUND)
    
class MarkOrderReadyView(APIView):
    permission_classes = [IsAuthenticated]
    def patch(self, request):
        order_id = request.query_params.get('order_id')
        if not order_id:
            return api_response(data= "Missing 'order_id'", status_code=status.HTTP_400_BAD_REQUEST)

        try:
            order = Orders.objects.get(id=order_id)
        except Orders.DoesNotExist:
            return api_response(data= "Order not found", status_code=status.HTTP_404_NOT_FOUND)

        order.status = 'confirmed'
        order.save()  #Automatically update status

        return api_response(message= "Order marked ready and status set to 'confirmed'", status_code=status.HTTP_200_OK)


class MenuItemListView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request):
        queryset = MenuItem.objects.select_related('restaurant', 'category').all()

        if request.user.is_staff or request.user.is_superuser:
            queryset = queryset
        elif request.user.user_type == 'customer':
            queryset = queryset.filter(is_approved=True)

        

        # Get filter parameters
        name = request.query_params.get("name")
        category = request.query_params.get("category")
        restaurant = request.query_params.get("restaurant")

        # Apply filters
        if name:
            queryset = queryset.filter(Q(name__icontains=name) | Q(description__icontains=name))
        if category:
            queryset = queryset.filter(Q(menu_items__category__name__icontains=category) | Q(restaurant_type__icontains=category)).distinct()
        if restaurant:
            queryset = queryset.filter(restaurant=restaurant)

        
        
        # Choose serializer based on user type
        if request.user.is_staff or request.user.is_superuser:
            serializer_class = MenuItemSerializer
        elif request.user.user_type == 'customer':
            serializer_class = MenuItemCreateSerializer

        serializer = serializer_class(queryset, many=True)
        print(serializer.data)
        return api_response(
            data=serializer.data, 
            status_code=status.HTTP_200_OK
        ) if serializer.data else api_response(
            data={"message": "No Menu items found matching your criteria"},
            status_code=status.HTTP_404_NOT_FOUND
        )

    
class RestaurantOrderListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        
        if user.is_staff or user.is_superuser:
            # Admins see all orders
            restaurant_filter = {}
        else:
            if user.user_type != 'restaurant_owner':
                return api_response(
                    message="You are not authorized to view these orders.",
                    status_code=status.HTTP_403_FORBIDDEN
                )
            
            owned_restaurants = Restaurant.objects.filter(owner=user)
            if not owned_restaurants.exists():
                return api_response(
                    message="No restaurants found for this owner.",
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            # Get list of restaurant IDs for filtering
            restaurant_ids = list(owned_restaurants.values_list('id', flat=True))
            restaurant_filter = {'restaurant_id__in': restaurant_ids}

        # Get the latest version of each order
        latest_order_map = (
            Orders.objects
            .filter(**restaurant_filter)  # Apply restaurant filter here
            .values('order_code')
            .annotate(latest_created=Max('created_at'))
        )

        # Build query for latest orders
        latest_q = Q()
        for entry in latest_order_map:
            latest_q |= Q(order_code=entry['order_code'], created_at=entry['latest_created'])

        # Main query with all conditions
        orders = Orders.objects.filter(
            latest_q,
            Q(status='pending') | 
            Q(payment_method_type='cash_on_delivery', payment_status='authorized') |
            Q(payment_method_type='razorpay', payment_status='paid')
        ).exclude(
            status__in=['cancelled', 'delivered']
        ).select_related(
            'restaurant', 'user'
        ).prefetch_related(
            'order_items'
        ).order_by('-created_at')

        serializer = OrderSerializer(orders, many=True)
        
        return api_response(
            status_code=status.HTTP_200_OK,
            data=serializer.data,
            message="No live orders found." if not serializer.data else None
        )
        
        
class OfferCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        
        if not (request.user.is_staff or request.user.is_superuser or request.user.user_type == 'restaurant_owner'):
            return api_response(data="Only admins or restaurant owners can create offers",
                             status_code=status.HTTP_403_FORBIDDEN)
            
        serializer = OfferSerializer(data=request.data )
        if serializer.is_valid():
            serializer.save()
            return api_response(data=serializer.data, status_code=status.HTTP_201_CREATED)
        return api_response(data=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

