from datetime import timezone
from decimal import Decimal
import json
from uuid import UUID
import razorpay
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from delivery import settings
from .models import Cart, Orders, OrderItem
from .serializer import CartCreateSerializer, CartItemUpdateSerializer, CartSerializer, OrderSerializer, OrderItemSerializer
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from user.models import SavedAddress
from django.db.models import Max, Q
from collections import defaultdict
from django.db import transaction
from django.views.decorators.csrf import csrf_exempt


class CartCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        
        user = request.user

        if user.user_type != 'customer':
            return Response({"error": "Only customers can view their cart."}, status=status.HTTP_403_FORBIDDEN)
        
        
        serializer = CartCreateSerializer(data=request.data)
        if serializer.is_valid():
            menu_item = serializer.validated_data['menu_item']
            quantity = serializer.validated_data['quantity']

            cart_item, created = Cart.objects.get_or_create(
                user=request.user, menu_item=menu_item,
                defaults={'quantity': quantity}
            )

            if not created:
                cart_item.quantity += quantity
                cart_item.save()

            return Response({"message": "Cart updated successfully."}, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CartListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        if user.user_type != 'customer':
            return Response({"error": "Only customers can view their cart."}, status=403)

        cart_items = Cart.objects.select_related('menu_item__restaurant').filter(user=user)
        grouped = {}

        for item in cart_items:
            restaurant = item.menu_item.restaurant
            rest_id = restaurant.id

            if rest_id not in grouped:
                grouped[rest_id] = {
                    "restaurant_id": rest_id,
                    "restaurant_name": restaurant.name,
                    "items": [],
                    "total": Decimal('0.00')
                }

            serializer = CartSerializer(item, context={"request": request})
            data = serializer.data

            grouped[rest_id]["items"].append(data)
            discounted_total = Decimal(data.get("discounted_total", "0.00"))
            grouped[rest_id]["total"] += discounted_total

        for group in grouped.values():
            group["total"] = round(group["total"], 2)

        return Response(list(grouped.values()))

class CartItemUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        
        user = request.user

        if user.user_type != 'customer':
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

        if user.user_type != 'customer':
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
    
class OrderListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        
        if user.user_type != "customer":
            return Response({"error": "Only customers can access their order list."}, status=status.HTTP_403_FORBIDDEN)

        user_orders = Orders.objects.filter(user=user).order_by('-placed_at')
        serialized_orders = OrderSerializer(user_orders, many=True)
        return Response(serialized_orders.data, status=status.HTTP_200_OK)

class OrderCreateView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        user = request.user

        if user.user_type != 'customer':
            return Response({"error": "Only customers can place Orders."}, status=status.HTTP_403_FORBIDDEN)

        cart_items = Cart.objects.filter(user=user)
        if not cart_items.exists():
            return Response({"error": "Cart is empty"}, status=status.HTTP_400_BAD_REQUEST)

        # Group cart items by restaurant
        restaurant_groups = {}
        for item in cart_items:
            rest = item.menu_item.restaurant
            restaurant_groups.setdefault(rest.id, {
                "restaurant": rest,
                "items": []
            })["items"].append(item)

        selected_restaurant_id = request.data.get("restaurant_id")
        payment_method = request.data.get("razor_pay", "cash_on_delivery")

        if selected_restaurant_id:
            try:
                selected_restaurant_id = UUID(selected_restaurant_id)
                if selected_restaurant_id not in restaurant_groups:
                    return Response({"error": "Invalid restaurant_id"}, status=status.HTTP_400_BAD_REQUEST)
                groups_to_process = {selected_restaurant_id: restaurant_groups[selected_restaurant_id]}
            except ValueError:
                return Response({"error": "Invalid restaurant_id format"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            groups_to_process = restaurant_groups

        # Address validation
        address_id = request.query_params.get('address_id') or request.data.get('address_id')
        if not address_id:
            return Response({"error": "address_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            saved_address = SavedAddress.objects.get(id=address_id, user=user)
        except SavedAddress.DoesNotExist:
            return Response({"error": "Address not found."}, status=status.HTTP_404_NOT_FOUND)

        created_orders = []

        for rest_id, group in groups_to_process.items():
            restaurant = group["restaurant"]
            items = group["items"]
            total_amount = sum(i.menu_item.price * i.quantity for i in items)

            # Create order with payment details
            order = Orders.objects.create(
                user=user,
                restaurant=restaurant,
                delivery_address=saved_address,
                total_amount=total_amount,
                payment_method_type=payment_method,
                amount_authorized=total_amount,
                metadata={
                    'restaurant_id': str(restaurant.id),
                    'address_id': str(saved_address.id)
                }
            )

            # Create order items
            for cart_item in items:
                OrderItem.objects.create(
                    order=order,
                    menu_item=cart_item.menu_item,
                    quantity=cart_item.quantity,
                    price=cart_item.menu_item.price
                )

            # Initiate payment if not cash on delivery
            if payment_method != 'cash_on_delivery':
                if not order.initiate_payment(total_amount):
                    return Response({
                        'error': 'Payment initiation failed',
                        'details': order.last_error
                    }, status=status.HTTP_400_BAD_REQUEST)

            created_orders.append(order)
            Cart.objects.filter(id__in=[i.id for i in items]).delete()

        response_data = {
            "message": "Order created successfully",
            "orders": OrderSerializer(created_orders, many=True).data
        }

        if payment_method == 'razorpay':
            response_data['payment_info'] = [{
                'order_id': str(order.id),
                'payment_context': order.get_razorpay_checkout_context()
            } for order in created_orders]

        return Response(response_data, status=status.HTTP_201_CREATED)

class CancelOrderView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        order_id = request.data.get('order_id')

        if not order_id:
            return Response({"error": "Order ID is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            original_order = Orders.objects.get(id=order_id, user=request.user)
        except Orders.DoesNotExist:
            return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)
        
        if original_order.status in ['confirmed','out_for_delivery']:
            return Response({'message':"Order cannot be cancelled after confirmed."})

        # Check if latest status is already 'cancelled' or 'delivered'
        latest_order = Orders.objects.filter(order_code=original_order.order_code).order_by('-created_at').first()
        if latest_order.status in ['delivered', 'cancelled']:
            return Response({"error": f"Order already {latest_order.status}"}, status=status.HTTP_400_BAD_REQUEST)

        # Restore items to cart
        for item in latest_order.order_items.all():
            cart_item, created = Cart.objects.get_or_create(
                user=request.user,
                menu_item=item.menu_item,
                defaults={'quantity': item.quantity}
            )
            if not created:
                cart_item.quantity += item.quantity
                cart_item.save()

        cancelled_order = Orders.objects.create(
            user=latest_order.user,
            restaurant=latest_order.restaurant,
            order_code=latest_order.order_code,
            status='cancelled',
            total_amount=latest_order.total_amount,
        )

        for item in latest_order.order_items.all():
            cancelled_order.order_items.create(
                menu_item=item.menu_item,
                quantity=item.quantity,
                price=item.price
            )

        return Response({"message": "Order cancelled and items added back to cart."}, status=status.HTTP_200_OK)

    
class DeleteFinalizedOrdersByOrderCodeView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        user = request.user

        latest_orders = (
            Orders.objects
            .filter(user=user)
            .values('order_code')
            .annotate(latest_created_at=Max('created_at'))
        )

        # Step 2: Identify order_codes where the latest status is cancelled or delivered
        deletable_codes = []
        for entry in latest_orders:
            order = Orders.objects.filter(
                user=user,
                order_code=entry['order_code'],
                created_at=entry['latest_created_at']
            ).first()
            if order and order.status in ['cancelled', 'delivered']:
                deletable_codes.append(order.order_code)

        # Step 3: Delete all orders with those order_codes
        deleted_count, _ = Orders.objects.filter(
            user=user,
            order_code__in=deletable_codes
        ).delete()

        return Response(
            {"message": f"{deleted_count} orders deleted for finalized order_codes."},
            status=status.HTTP_200_OK
        )
        
        
class RazorpayCallbackView(APIView):
    permission_classes = [IsAuthenticated]

    @csrf_exempt
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request):
        try:
            # Verify webhook signature
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
            body = request.body.decode('utf-8')
            signature = request.headers.get('X-Razorpay-Signature')
            
            client.utility.verify_webhook_signature(
                body,
                signature,
                settings.RAZORPAY_WEBHOOK_SECRET
            )
            
            data = json.loads(body)
            event = data['event']
            payment_data = data['payload']['payment']['entity']

            # Find the order
            order = Orders.objects.get(
                gateway_transaction_id=payment_data['order_id'],
                user=request.user
            )
            
            if event == 'payment.authorized':
                order.payment_status = 'authorized'
                order.payment_authorized_at = timezone.now()
                order.save()
                
            elif event == 'payment.captured':
                order.payment_status = 'captured'
                order.payment_captured_at = timezone.now()
                order.amount_captured = payment_data['amount'] / 100
                order.save()
                
            return Response({'status': 'success'})
            
        except Exception as e:
            return Response(
                {'status': 'error', 'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )