from django.utils import timezone
from decimal import Decimal
import hashlib
import hmac
import json
from uuid import UUID
import razorpay
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from common.response import api_response
from delivery.settings import RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET, RAZORPAY_WEBHOOK_URL, RAZORPAY_WEBHOOK_SECRET
from .models import Cart, Orders, OrderItem
from .serializer import CartCreateSerializer, CartItemUpdateSerializer, CartSerializer, OrderSerializer, OrderItemSerializer
from django.shortcuts import get_object_or_404, redirect, render
from rest_framework.permissions import IsAuthenticated
from user.models import SavedAddress
from django.db.models import Max, Q
from collections import defaultdict
from django.db import transaction
from django.views.decorators.csrf import csrf_exempt
from common.types import PAYMENT_METHOD_CHOICES
import logging
logger = logging.getLogger(__name__) 
from django.http import HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt



class CartCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        
        user = request.user

        if not( user.user_type == 'customer' or user.is_staff or user.is_superuser):
            return api_response(message = "Only customers can view their cart.", status_code=status.HTTP_403_FORBIDDEN)
        
        
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

            return api_response(message= "Cart updated successfully.", status_code=status.HTTP_201_CREATED)

        return api_response(data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

class CartListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        if not( user.user_type == 'customer' or user.is_staff or user.is_superuser):
            return api_response(message = "Only customers can view their cart.", status_code=status.HTTP_403_FORBIDDEN)

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

        return api_response(data = list(grouped.values()), status_code=status.HTTP_200_OK)

class CartItemUpdateDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        
        user = request.user

        if not( user.user_type == 'customer' or user.is_staff or user.is_superuser):
            return api_response(message = "Only customers can view their cart.", status_code=status.HTTP_403_FORBIDDEN)
        
        
        cart_item_id = request.query_params.get("id")
        if not cart_item_id:
            return api_response(message = "Cart item ID is required", status_code=status.HTTP_400_BAD_REQUEST)

        try:
            cart_item = Cart.objects.get(id=cart_item_id, user=request.user)
        except Cart.DoesNotExist:
            return api_response(message = "Cart item not found", status_code=status.HTTP_404_NOT_FOUND)

        serializer = CartSerializer(cart_item, data=request.data, partial=True)
        if serializer.is_valid():
            if serializer.validated_data.get("quantity") == 0:
                cart_item.delete()
                return api_response(message= "Cart item deleted because quantity was 0", status_code=status.HTTP_204_NO_CONTENT)

            serializer.save()
            return api_response(data = serializer.data, status_code=status.HTTP_200_OK)
        return api_response(data = serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request):
        
        user = request.user

        if not( user.user_type == 'customer' or user.is_staff or user.is_superuser):
            return api_response(message = "Only customers can view their cart.", status_code=status.HTTP_403_FORBIDDEN)
        
        
        cart_item_id = request.query_params.get("id")
        if not cart_item_id:
            return api_response(message = "Cart item ID is required", status_code=status.HTTP_400_BAD_REQUEST)

        try:
            cart_item = Cart.objects.get(id=cart_item_id, user=request.user)
            cart_item.delete()
            return api_response(message= "Cart item deleted", status_code=status.HTTP_204_NO_CONTENT)
        except Cart.DoesNotExist:
            return api_response(message = "Cart item not found", status_code=status.HTTP_404_NOT_FOUND)
    

    
class OrderListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        
        if not( user.user_type == 'customer' or user.is_staff or user.is_superuser):
            return api_response(message = "Only customers can access their order list.", status_code=status.HTTP_403_FORBIDDEN)

        user_orders = Orders.objects.filter(user=user).order_by('-created_at')
        serialized_orders = OrderSerializer(user_orders, many=True)
        print(serialized_orders)
        return api_response(
            data={
            "orders": serialized_orders.data,
            "key_id": RAZORPAY_KEY_ID,
            },
            status_code=status.HTTP_200_OK
        )

class OrderCreateView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        user = request.user

        if not( user.user_type == 'customer' or user.is_staff or user.is_superuser):
            return api_response(message = "Only customers can place orders.", 
                          status_code=status.HTTP_403_FORBIDDEN)

        cart_items = Cart.objects.filter(user=user)
        if not cart_items.exists():
            return api_response(message = "Cart is empty", 
                          status_code=status.HTTP_400_BAD_REQUEST)

        # Validate address
        address_id = request.data.get('address_id')
        if not address_id:
            return api_response(message = "address_id is required",
                          status_code=status.HTTP_400_BAD_REQUEST)

        try:
            saved_address = SavedAddress.objects.get(id=address_id, user=user)
        except SavedAddress.DoesNotExist:
            return api_response(message = "Address not found",
                          status_code=status.HTTP_404_NOT_FOUND)

        # Group cart items by restaurant
        restaurant_groups = {}
        for item in cart_items:
            restaurant = item.menu_item.restaurant
            restaurant_groups.setdefault(restaurant.id, {
                "restaurant": restaurant,
                "items": []
            })["items"].append(item)

        # Process selected restaurant or all
        selected_restaurant_id = request.data.get("restaurant_id")
        if selected_restaurant_id:
            try:
                selected_restaurant_id = UUID(selected_restaurant_id)
                if selected_restaurant_id not in restaurant_groups:
                    return api_response(message = "Invalid restaurant_id",
                                  status_code=status.HTTP_400_BAD_REQUEST)
                groups_to_process = {selected_restaurant_id: restaurant_groups[selected_restaurant_id]}
            except ValueError:
                return api_response(message = "Invalid restaurant_id format",
                              status_code=status.HTTP_400_BAD_REQUEST)
        else:
            groups_to_process = restaurant_groups

        payment_method = request.data.get("payment_method", "cash_on_delivery")
        if payment_method not in dict(PAYMENT_METHOD_CHOICES):
            return api_response(message = "Invalid payment method",
                          status_code=status.HTTP_400_BAD_REQUEST)

        created_orders = []

        for rest_id, group in groups_to_process.items():
            restaurant = group["restaurant"]
            items = group["items"]
            total_amount = sum(i.menu_item.price * i.quantity for i in items)

            # Create order
            order = Orders.objects.create(
                user=user,
                restaurant=restaurant,
                delivery_address=str(saved_address),
                total_amount=total_amount,
                payment_method_type=payment_method,
                amount_authorized=total_amount,
                metadata={
                    'restaurant_id': str(restaurant.id),
                    'address_id': str(saved_address.id),
                    'cart_items': [str(item.id) for item in items]
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

            # Handle payment initiation
            if payment_method == 'razorpay':
                payment_context = order.create_razorpay_order(total_amount)
                if not payment_context:
                    return api_response(message={
                        'error': 'Payment initiation failed',
                        'details': order.last_error}
                    , status_code=status.HTTP_400_BAD_REQUEST)
            else:  # cash_on_delivery
                order.payment_method_type =  "cash_on_delivery"
                order.payment_status = 'authorized'

            created_orders.append(order)
            cart_items.filter(id__in=[i.id for i in items]).delete()

        # Prepare response
        response_data = {
            "message": "Order(s) created successfully",
            "orders": OrderSerializer(created_orders, many=True).data
        }

        if payment_method == 'razorpay':
            try:
                payment_context = order.create_razorpay_order(total_amount)
                if not payment_context:
                    return api_response(message = {
                        'error': 'Payment initiation failed',
                        'details': 'Could not create Razorpay order'}
                    , status_code=status.HTTP_400_BAD_REQUEST)
                    
                response_data['payment_info'] = {
                    'order_id': str(order.id),
                    'razorpay_order_id': order.razorpay_order_id,
                    'amount': total_amount,
                    'currency': 'INR',
                    'key_id': RAZORPAY_KEY_ID
                }
                
            except Exception as e:
                return api_response(message={
                    'error': 'Payment processing failed',
                    'details': str(e)}
                , status_code=status.HTTP_400_BAD_REQUEST)
        
        return api_response(data = response_data, status_code=status.HTTP_201_CREATED)
class CancelOrderView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        
        user=request.user
        if not( user.user_type == 'customer' or user.is_staff or user.is_superuser):
            return api_response(message = "Only customers can cancel their orders.", 
                          status_code=status.HTTP_403_FORBIDDEN)
        
        order_id = request.data.get('order_id')

        if not order_id:
            return api_response(message = "Order ID is required", status_code=status.HTTP_400_BAD_REQUEST)

        try:
            original_order = Orders.objects.get(id=order_id, user=user)
        except Orders.DoesNotExist:
            return api_response(message = "Order not found", status_code=status.HTTP_404_NOT_FOUND)
        
        if original_order.status in ['confirmed','out_for_delivery']:
            return api_response(message="Order cannot be cancelled after confirmed.", status_code=status.HTTP_405_METHOD_NOT_ALLOWED)

        # Check if latest status is already 'cancelled' or 'delivered'
        latest_order = Orders.objects.filter(order_code=original_order.order_code).order_by('-created_at').first()
        if latest_order.status in ['delivered', 'cancelled']:
            return api_response(message = f"Order already {latest_order.status}", status_code=status.HTTP_400_BAD_REQUEST)

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

        return api_response(message= "Order cancelled and items added back to cart.", status_code=status.HTTP_200_OK)

    
class DeleteFinalizedOrdersByOrderCodeView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        user = request.user
        
        if not(user.user_type == 'customer' or user.is_staff or user.is_superuser):
            return api_response(message = "Only customers can place orders.", 
                          status_code=status.HTTP_403_FORBIDDEN)
        
        order_id = request.data.get("order_id")
        
        if order_id:
            deleted_count, _ = Orders.objects.filter(
            user=user,
            id = order_id).delete()
            return api_response(message= f"{deleted_count} Order(s) deleted",status_code=status.HTTP_200_OK)

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

        return api_response(
            message= f"{deleted_count} orders deleted for finalized order_codes.",
            status_code=status.HTTP_200_OK
        )
        
        


def payment_page(request, order_id):
    order = get_object_or_404(Orders, id=order_id, user=request.user)
    return render(request, 'registration/payment_page.html', {'order': order})


    
@csrf_exempt 

def razorpay_webhook(request):
    if request.method != 'POST':
        return HttpResponseBadRequest("Invalid request method")
    
    try:
        # 1. Verify the webhook signature
        payload = request.body.decode('utf-8')
        received_signature = request.headers.get('X-Razorpay-Signature')
        print(payload)
        print(received_signature)
        
        expected_signature = hmac.new(
            RAZORPAY_WEBHOOK_SECRET.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
        print(expected_signature)
        
        # Compare signatures (remove 'sha256=' prefix if present)
        if not hmac.compare_digest(expected_signature, received_signature.replace('sha256=', '')):
            return HttpResponseBadRequest("Invalid signature")
        
        
        # 2. Process the event
        data = json.loads(payload)
        event = data.get('event')
        
        if event == 'order.paid':  
            order_data = data['payload']['order']['entity']
            razorpay_order_id = data['payload']['order']['entity']['id']
            
            # 3. Update your order
            try:
                order = Orders.objects.get(razorpay_order_id=razorpay_order_id)
                order.payment_status = 'paid'  
                order.payment_captured_at = timezone.now()
                order.amount_captured = order_data['amount'] / 100  # Convert paise to INR
                order.save()
                
            except Orders.DoesNotExist:
                logger.error(f"Order not found for Razorpay ID: {razorpay_order_id}")
                
        return HttpResponse("OK", status=200)
        
    except razorpay.errors.SignatureVerificationError:
        return HttpResponseBadRequest("Invalid signature")
    except Exception as e:
        logger.exception("Webhook processing failed")
        return HttpResponseBadRequest("Error processing webhook")

