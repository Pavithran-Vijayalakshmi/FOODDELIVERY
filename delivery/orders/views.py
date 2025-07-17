from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Cart, orders, OrderItem
from .serializer import CartCreateSerializer, CartItemUpdateSerializer, CartSerializer, OrderSerializer, OrderItemSerializer
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from user.models import SavedAddress


class CartCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        
        user = request.user

        if user.user_type != 'Customer':
            return Response({"error": "Only customers can view their cart."}, status=status.HTTP_403_FORBIDDEN)
        
        
        serializer = CartCreateSerializer(data=request.data)
        if serializer.is_valid():
            menu_item = serializer.validated_data['menu_item']
            quantity = serializer.validated_data['quantity']

            # Check if cart item already exists for this user and menu item
            cart_item, created = Cart.objects.get_or_create(
                user=request.user, menu_item=menu_item,
                defaults={'quantity': quantity}
            )

            if not created:
                # If already exists, update the quantity
                cart_item.quantity += quantity
                cart_item.save()

            return Response({"message": "Cart updated successfully."}, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CartListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        if user.user_type != 'Customer':
            return Response({"error": "Only customers can view their cart."}, status=status.HTTP_403_FORBIDDEN)

        cart_items = Cart.objects.filter(user=user)
        serializer = CartSerializer(cart_items, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    
class CartItemUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        
        user = request.user

        if user.user_type != 'Customer':
            return Response({"error": "Only customers can view their cart."}, status=status.HTTP_403_FORBIDDEN)
        
        
        cart_item_id = request.query_params.get("id")
        if not cart_item_id:
            return Response({"error": "Cart item ID is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            cart_item = Cart.objects.get(id=cart_item_id, user=request.user)
        except Cart.DoesNotExist:
            return Response({"error": "Cart item not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = CartSerializer(cart_item, data=request.data, partial=True)
        if serializer.is_valid():
            if serializer.validated_data.get("quantity") == 0:
                cart_item.delete()
                return Response({"message": "Cart item deleted because quantity was 0"}, status=status.HTTP_204_NO_CONTENT)

            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CartItemDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        
        user = request.user

        if user.user_type != 'Customer':
            return Response({"error": "Only customers can view their cart."}, status=status.HTTP_403_FORBIDDEN)
        
        
        cart_item_id = request.query_params.get("id")
        if not cart_item_id:
            return Response({"error": "Cart item ID is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            cart_item = Cart.objects.get(id=cart_item_id, user=request.user)
            cart_item.delete()
            return Response({"message": "Cart item deleted"}, status=status.HTTP_204_NO_CONTENT)
        except Cart.DoesNotExist:
            return Response({"error": "Cart item not found"}, status=status.HTTP_404_NOT_FOUND)



class OrderDetailView(APIView):
    def get(self, request, pk):
        order = get_object_or_404(orders, pk=pk)
        serializer = OrderSerializer(order)
        return Response(serializer.data)

    def put(self, request, pk):
        order = get_object_or_404(orders, pk=pk)
        serializer = OrderSerializer(order, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        order = get_object_or_404(orders, pk=pk)
        order.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class OrderItemListCreateView(APIView):
    def get(self, request):
        items = OrderItem.objects.all()
        serializer = OrderItemSerializer(items, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = OrderItemSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class OrderItemDetailView(APIView):
    def get(self, request, pk):
        item = get_object_or_404(OrderItem, pk=pk)
        serializer = OrderItemSerializer(item)
        return Response(serializer.data)

    def put(self, request, pk):
        item = get_object_or_404(OrderItem, pk=pk)
        serializer = OrderItemSerializer(item, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        item = get_object_or_404(OrderItem, pk=pk)
        item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    
class OrderListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        
        # Allow only customers to access this endpoint
        if user.user_type != "Customer":
            return Response({"error": "Only customers can access their order list."}, status=status.HTTP_403_FORBIDDEN)

        user_orders = orders.objects.filter(user=user).order_by('-placed_at')
        serialized_orders = OrderSerializer(user_orders, many=True)
        return Response(serialized_orders.data, status=status.HTTP_200_OK)
    


class OrderCreateView(APIView): 
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

        if user.user_type != 'Customer':
            return Response({"error": "Only customers can place orders."}, status=status.HTTP_403_FORBIDDEN)

        cart_items = Cart.objects.filter(user=user)
        if not cart_items.exists():
            return Response({"error": "Cart is empty"}, status=status.HTTP_400_BAD_REQUEST)

        # Get address_id from query params or request body
        address_id = request.query_params.get('address_id') or request.data.get('address_id')
        if not address_id:
            return Response({"error": "address_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            saved_address = SavedAddress.objects.get(id=address_id, user=user)
        except SavedAddress.DoesNotExist:
            return Response({"error": "Address not found."}, status=status.HTTP_404_NOT_FOUND)

        delivery_address = saved_address.address

        # Group cart items by restaurant
        restaurant_groups = {}
        for item in cart_items:
            rest_id = item.menu_item.restaurant.id
            restaurant_groups.setdefault(rest_id, []).append(item)

        created_orders = []

        for rest_id, items in restaurant_groups.items():
            restaurant = items[0].menu_item.restaurant
            total_amount = sum(i.menu_item.price * i.quantity for i in items)

            # Create order
            order = orders.objects.create(
                user=user,
                restaurant=restaurant,
                total_amount=total_amount,
                delivery_address=delivery_address
            )

            # Create order items
            for cart_item in items:
                OrderItem.objects.create(
                    order=order,
                    menu_item=cart_item.menu_item,
                    quantity=cart_item.quantity,
                    price=cart_item.menu_item.price
                )

            created_orders.append(order)

        # Clear the cart after order placement
        cart_items.delete()

        serialized_orders = OrderSerializer(created_orders, many=True)
        return Response({"message": "Orders placed successfully", "orders": serialized_orders.data}, status=status.HTTP_201_CREATED)

class CancelOrderView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        order_id = request.data.get('order_id')

        if not order_id:
            return Response({"error": "Order ID is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            order = orders.objects.get(id=order_id, user=request.user)
        except orders.DoesNotExist:
            return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)

        if order.status in ['delivered', 'cancelled']:
            return Response({"error": f"Order already {order.status}"}, status=status.HTTP_400_BAD_REQUEST)

        # Add items back to cart
        for item in order.order_items.all():
            cart_item, created = Cart.objects.get_or_create(
                user=request.user,
                menu_item=item.menu_item,
                defaults={'quantity': item.quantity}
            )
            if not created:
                cart_item.quantity += item.quantity
                cart_item.save()

        # Cancel the order
        order.status = 'cancelled'
        order.save()

        return Response({"message": "Order cancelled and items added back to cart."}, status=status.HTTP_200_OK)
